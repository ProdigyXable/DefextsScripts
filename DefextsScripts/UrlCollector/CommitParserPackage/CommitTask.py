from HelperUtility.Log import Log

import git
import gc
import shutil
import os

class CommitTask ( object ):
    """Class details to be changed later"""
    logger = None

    TEMP_FOLDER_NAME = None # Path of temp folder used to hold repository
    CURRENT_BRANCH = None # Current branch

    # --- Various Filter Criteria--- #
    KEYWORDS = None # List of keywords to be searched for within individual commits
    FILE_TYPES = None
    MAX_FILE_MODIFIED_LIMIT = None
    MAX_LINES_CHANGED_PER_FILE = None
    ACCEPTABLE_BUILD_SYSTEM_FILES = None

    COUNT = 0 # Used to determine the 'name' of the thread
    NAME = None

    BYPASS_CREDENTIALS = "null:null@"

    def __init__ ( self, log: Log, keywords, file_types, max_diff_limit, changes_per_file, build_systems ):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = "T{}".format( CommitTask.COUNT )
        self.TEMP_FOLDER_NAME = "temp-{}".format( self.NAME )

        self.logger = log
        self.KEYWORDS = keywords
        self.FILE_TYPES = file_types
        self.MAX_FILE_MODIFIED_LIMIT = max_diff_limit
        self.MAX_LINES_CHANGED_PER_FILE = changes_per_file
        self.ACCEPTABLE_BUILD_SYSTEM_FILES = build_systems

    # --- LOGGER HELPER METHODS [START] --- #
    def info ( self, message ):
        if self.logger is None:
            return

        self.logger.info( "\t[{}]\t {}".format( self.NAME, message ) )

    def warning ( self, message ):
        if self.logger is None:
            return

        self.logger.warning( "\t[{}]\t {}".format( self.NAME, message ) )

    def detailed ( self, message ):
        if self.logger is None:
            return

        self.logger.detailed( "\t[{}]\t {}".format( self.NAME, message ) )

    def debug ( self, message ):
        if self.logger is None:
            return

        self.logger.debug( "\t[{}]\t {}".format( self.NAME, message ) )

    def print ( self, message ):
        if self.logger is None:
            return

        self.logger.minimal( "\t[{}]\t {}".format( self.NAME, message ) )
    # --- LOGGER HELPER METHODS [END] --- #

    # Entry point for each CommitTask as it enters its own thread
    def begin ( self, project ):
        checked_commits = set()
        satisfactory_commits = set()

        self.info( "Processing '{}'".format( project ) )
        
        original_repo = self.downloadProject( project )
        branches = self.getBranches( project, original_repo )

        for branch in branches:
            self.CURRENT_BRANCH = self.checkoutBranch( original_repo, project, branch )
            commits = self.getCommits( project, original_repo )

            # Employ various filters
            filtered_commits = self.filter( original_repo, project, commits, checked_commits )

            checked_commits.update( commits )
            satisfactory_commits.update( filtered_commits )

            self.debug( "{} commits currently accumulated".format( len( satisfactory_commits ) ) )

        self.info( "{} unique satisfactory commits found from {} branches".format( len( satisfactory_commits ), len( branches ) ) )

        self.end( original_repo )
        return ( project, satisfactory_commits )

    def filter ( self, repo, project, commits, checked_commits ) :
        filtered_commits = None

        # For efficiency, only checked commits we have not already looked at
        unchecked_commits = list( filter( lambda com: CommitTask.getUncheckedCommits( com, checked_commits ), commits ) )
        unchecked_commits_length = len( unchecked_commits )

        skipped_commits_length = len( commits ) - len( unchecked_commits ) 
        
        if( skipped_commits_length > 0 ):
            self.detailed( "Skipping over {} commits".format( skipped_commits_length ) )
        
        if ( unchecked_commits_length > 0 ):
            filter1_commits = self.filterCommitsOnKeywords( project, unchecked_commits ) # Stage 1 filtering
            filter2_commits = self.filterCommitsOnDiffFiles( repo, project , filter1_commits ) # Stage 2 filtering
            filter3_commits = self.filterCommitsOnBuildSystem( repo, project, filter2_commits ) # Stage 3 filtering

            filtered_commits = filter3_commits 
        else:
            filtered_commits = [] # Empty list

        if( unchecked_commits_length ):
            self.detailed( "{} / {} new commits successfully filtered + collected".format( len( filtered_commits ), unchecked_commits_length ) )
        return filtered_commits

    def filterCommitsOnDiffFiles ( self, repo, project, commits ):
        if len( commits ) == 0:
            return commits
        else:
            satisfactory_commits = []
        
            for commit in commits:
                previous_commit = repo.commit( "{}~1".format( commit ) ) # Get previous commit
                diffs = previous_commit.diff( commit, create_patch=True ) # Acquire diff
            
                # Filter based on number of files modified [BEGIN]
                diff_filecount_criteria_result = len( diffs ) > self.MAX_FILE_MODIFIED_LIMIT # Determine if commit should be excluded

                if diff_filecount_criteria_result:
                    self.detailed( "[{}] excluded: Too many files modified: {} > {}".format( commit, len( diffs ), self.MAX_FILE_MODIFIED_LIMIT ) )
                    continue
                # Filter based on number of files modified [END]

                # If any modified file type does not match an approved
                # extension, continue to next loop iteration
                do_not_add_commit = False
                for diff in diffs:
                    assert ( not diff.a_path is None ) or ( not diff.b_path is None ), "Both diff paths are None"

                    if ( self.filterFileExtension( commit, diff ) or self.filterLinesModified( commit, diff ) ):
                        do_not_add_commit = True
                        break


                if do_not_add_commit:
                    do_not_add_commit = False
                    continue

                self.detailed( "[{}] accepted".format( commit ) )
                satisfactory_commits.append( commit )
            self.debug( "{} / {} commits accepted for diff-based criteria".format( len( satisfactory_commits ), len( commits ) ) )
            return satisfactory_commits

    
    # Filter based on modified file extension(s)
    def filterFileExtension ( self, commit, diff ):
        
        stop_iteration_a, file_a_extension = self.determineFileExtension( diff.a_path )
        stop_iteration_b, file_b_extension = self.determineFileExtension( diff.b_path )

        if stop_iteration_a or stop_iteration_b:
            self.detailed( "[{}] excluded: Unapproved file types: {}/{}".format( commit, file_a_extension, file_b_extension ) )
            return True

        return False

    # Given a path to a file, determines if the file's extension is allowed
    # True = not allowed, False = allowed
    def determineFileExtension ( self, diff_path ):
        if( diff_path is None ):
            return False, None
        else:
            file_extension = diff_path.split( "." )[ -1 ]
            return not file_extension in self.FILE_TYPES, file_extension

    # Filter based on lines modified for a diff
    def filterLinesModified ( self, commit, diff ):
        
        diff_data_lines = diff.diff.decode( "utf-8" ).split( "\n" ) # Puts diff into human readable array with classic diff format

        lines_added = list( filter( lambda line_string: line_string.startswith( "+" ) and len( line_string.strip() ) > 1, diff_data_lines ) ) # Get list of added lines
        lines_deleted = list( filter( lambda line_string: line_string.startswith( "-" ) and len( line_string.strip() ) > 1, diff_data_lines ) ) # Get list of deleted lines
                
        if( ( len( lines_added ) + len( lines_deleted ) ) > self.MAX_LINES_CHANGED_PER_FILE ):
            self.detailed( "[{}] excluded: Too many changes within one file: {} > {}".format( commit, len( lines_added ) + len( lines_deleted ), self.MAX_LINES_CHANGED_PER_FILE ) )
            return True
        else:
            return False

    def filterCommitsOnBuildSystem ( self, repo, project, commits ):
        if len( commits ) == 0:
            return commits
        else:
            satisfactory_commits = []
            for commit in commits:
                self.detailed( "Checking [{}]'s build system".format( commit ) )
                if self.checkBuildSystem( repo, commit ):
                    satisfactory_commits.append( commit )
                repo.git.reset( "--hard" ) # Reset to ensure local branch reflects remote branch

            self.debug( "{} / {} commits accepted on build system criteria".format( len( satisfactory_commits ), len( commits ) ) )
            return satisfactory_commits

    def checkBuildSystem ( self, repo, commit ):
        repo.git.checkout( commit )
        for current_path, folders, files in os.walk( self.TEMP_FOLDER_NAME ):
            found_build_system_files = self.ACCEPTABLE_BUILD_SYSTEM_FILES.intersection( files )
            if len( found_build_system_files ) > 0:
                return True
        return False

    def filterCommitsOnKeywords ( self, project, commits ):
        if len( commits ) == 0:
            return commits
        else:
            # Return only commits containing any queried keywords
            satisfactory_commits = list( filter( lambda new_commit: CommitTask.findKeywords( self.KEYWORDS, new_commit.message ), commits ) )
            return satisfactory_commits

    # Deletes temp folder used to hold repository
    def end ( self, repo ):
        gc.collect()
        repo.git.clear_cache()
        git.rmtree( self.TEMP_FOLDER_NAME )

        self.detailed( "ThreadTask has completed" )

    # Clones the given repository into a temp folder
    def downloadProject ( self, project ):
        self.detailed( "Downloading '{}'".format( project ) )

        if os.path.exists( self.TEMP_FOLDER_NAME ):
            git.rmtree( self.TEMP_FOLDER_NAME )

        bypass_project = project.replace( "https://github.com","https://{}github.com".format( self.BYPASS_CREDENTIALS ) )
        result = git.Repo.clone_from( bypass_project, self.TEMP_FOLDER_NAME )
        return result

    # Get list of (remote) branches for the given repository
    def getBranches ( self, project, repo ):
        branches = repo.remotes.origin.refs

        self.debug( "{} branches found for {}".format( len( branches ), project ) )
        return branches

    # Checkout the given branch
    def checkoutBranch ( self, repo, project, branch ):
        if( not self.CURRENT_BRANCH is None ):
            repo.git.clean( "-xdf" ) # Clean to ensure files from previously checkout branches are removed
            repo.git.checkout( self.CURRENT_BRANCH )
        old_branch = repo.active_branch
        repo.git.checkout( branch, b=branch.name )
        new_branch = repo.active_branch
        
        self.debug( "Changing branches: {} -> {}".format( old_branch, new_branch ) )
        return branch

    # Get list of commits for the current branch
    def getCommits ( self, project, repo ):
        result = list( repo.iter_commits() )
        
        self.detailed( "Retrieving {} commits from '{}'".format( len( result ), project ) )
        return result

    # Return elements not already in an accumulating set
    def getUncheckedCommits ( new_commit, checked_commits ):
        return not new_commit in checked_commits

    # Return any keyword is within message
    def findKeywords ( keywords, message ):
        message = message.lower()
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword in message:
                return True
        return False