from HelperUtility.log import Log

import git
import gc
import shutil
import os

class CommitTask ( object ):
    """Class details to be changed later"""
    logger = None

    TEMP_FOLDER_NAME = None # Path of temp folder used to hold repository

    # --- Various Filter Criteria--- #
    KEYWORDS = None # List of keywords to be searched for within individual commits
    FILE_TYPES = None
    MAX_FILE_MODIFIED_LIMIT = None
    MAX_LINES_CHANGED_PER_FILE = None

    COUNT = 0 # Used to determine the 'name' of the thread
    NAME = None

    def __init__ ( self, logger: Log, keywords, file_types, max_diff_limit, changes_per_file ):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = "T{}".format( CommitTask.COUNT )
        self.TEMP_FOLDER_NAME = "temp-{}".format( self.NAME )

        self.logger = logger
        self.KEYWORDS = keywords
        self.FILE_TYPES = file_types
        self.MAX_FILE_MODIFIED_LIMIT = max_diff_limit
        self.MAX_LINES_CHANGED_PER_FILE = changes_per_file

    # --- LOGGER HELPER METHODS [START] --- #
    def info ( self, message ):
        if self.logger is None:
            return

        self.logger.info( "\t\t<{}> {}".format( self.NAME, message ) )

    def warning ( self, message ):
        if self.logger is None:
            return

        self.logger.warning( "\t\t<{}> {}".format( self.NAME, message ) )

    def detailed ( self, message ):
        if self.logger is None:
            return

        self.logger.detailed( "\t\t<{}> {}".format( self.NAME, message ) )

    def debug ( self, message ):
        if self.logger is None:
            return

        self.logger.debug( "\t\t<{}> {}".format( self.NAME, message ) )

    def print ( self, message ):
        if self.logger is None:
            return

        self.logger.minimal( "\t\t<{}> {}".format( self.NAME, message ) )
    # --- LOGGER HELPER METHODS [END] --- #

    # Entry point for each CommitTask as it enters its own thread
    def begin ( self, project ):
        checked_commits = set()
        satisfactory_commits = set()

        self.detailed( "Processing '{}'".format( project ) )  
        
        original_repo = self.downloadProject( project )
        branches = self.getBranches( project, original_repo )

        for branch in branches:
            self.checkoutBranch( original_repo, project, branch )
            commits = self.getCommits( project, original_repo )

            # Emply various filters
            filtered_commits = self.filter( original_repo, project, commits, checked_commits )
            checked_commits.update( commits )

            satisfactory_commits.update( filtered_commits )

            self.debug( "{} commits currently accmulated".format( len( satisfactory_commits ) ) )

        self.info( "{} unique satisfactory commits found from {} branches".format( len( satisfactory_commits ), len( branches ) ) )

        self.end( original_repo )
        return ( project, satisfactory_commits )

    def filter ( self, repo, project, commits, checked_commits ) :
        filtered_commits = None
        # For efficiency, only checked commits we have not already looked at
        unchecked_commits = list( filter( lambda com: CommitTask.getUncheckedCommits( com, checked_commits ), commits ) )
        filter1_commits = self.filterCommitsOnKeywords( project, unchecked_commits )
        filter2_commits = self.filterCommitsOnDiffFiles( repo, project , filter1_commits )
        filter3_commits = self.filterCommitsOnBuildSystem( repo, project, filter2_commits )

        filtered_commits = filter3_commits

        self.detailed( "{} / {} new commits successfully filtered + collected".format( len( filtered_commits ), len( unchecked_commits ) ) )
        return  filtered_commits

    def filterCommitsOnDiffFiles ( self, repo, project, commits ):
        satisfactory_commits = []
        
        for commit in commits:
            previous_commit = repo.commit( "{}~1".format( commit ) ) # Get previous commit
            diffs = previous_commit.diff( commit, create_patch=True ) # Acquire diff
            
            # Filter based on number of files modified [BEGIN]
            diff_filecount_criteria_result = len( diffs ) > self.MAX_FILE_MODIFIED_LIMIT # Determine if commit should be excluded

            if diff_filecount_criteria_result:
                self.debug( "Commit {} excluded: Too many files modified: {} > {}".format( commit, len( diffs ), self.MAX_FILE_MODIFIED_LIMIT ) )
                continue
            # Filter based on number of files modified [END]

            # If any modified file type does not match an approved extension,
            # continue to next loop iteration
            do_not_add_commit = False
            for diff in diffs:  
                assert ( not diff.a_path is None ) or ( not diff.b_path is None ), "Both diff paths are None"

                # Filter based on modified file extension(s) [BEGIN]
                stop_iteration_a, file_a_extension = self.determineFileExtension( diff.a_path )
                stop_iteration_b, file_b_extension = self.determineFileExtension( diff.b_path )

                if stop_iteration_a or stop_iteration_b:
                    do_not_add_commit = True
                    self.debug( "Commit {} excluded: Unapproved file types: {}/{}".format( commit, file_a_extension, file_b_extension ) )
                    break
                # Filter based on extension [END]

                # Filter based on lines modified [BEGIN]
                diff_data_lines = diff.diff.decode( "utf-8" ).split( "\n" )  # Puts diff into human readable array with classic diff format
                lines_added = list( filter( lambda line_string: line_string.startswith( "+" ) and len( line_string.strip() ) > 1, diff_data_lines ) )
                lines_deleted = list( filter( lambda line_string: line_string.startswith( "-" ) and len( line_string.strip() ) > 1, diff_data_lines ) )
                
                
                if( ( len( lines_added ) + len( lines_deleted ) ) > self.MAX_LINES_CHANGED_PER_FILE ):
                    do_not_add_commit = True
                    self.debug( "Commit {} excluded: Too many changes within one file: {} > {}".format( commit, len( lines_added ) + len( lines_deleted ), self.MAX_LINES_CHANGED_PER_FILE ) )
                    break
                # Filter based on lines modified [BEGIN]

            if do_not_add_commit:
                do_not_add_commit = False
                continue

            self.debug( "Commit {} accepted".format( commit ) )
            satisfactory_commits.append( commit )
        self.detailed( "{} / {} commits added".format( len( satisfactory_commits ), len( commits ) ) )
        return satisfactory_commits

    # Given a path to a file, determines if the file's extension is allowed
    # True = not allowed, False = allowed
    def determineFileExtension ( self, diff_path ):
        if( diff_path is None ):
            return False, None
        else:
            file_extension = diff_path.split( "." )[ -1 ]
            return not file_extension in self.FILE_TYPES, file_extension

    def filterCommitsOnBuildSystem ( self, repo, project, commits ):
        result = None
        return result

    def filterCommitsOnKeywords ( self, project, commits ):
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
        self.debug( "Downloading '{}'".format( project ) )

        if os.path.exists( self.TEMP_FOLDER_NAME ):
            git.rmtree( self.TEMP_FOLDER_NAME )

        result = git.Repo.clone_from( project, self.TEMP_FOLDER_NAME )
        return result

    # Get list of (remote) branches for the given repository
    def getBranches ( self, project, repo ):
        result = repo.remotes.origin.refs

        self.debug( "{} branches found for {}".format( len( result ), project ) )
        return  result

    # Checkout the given branch
    def checkoutBranch ( self, repo, project, branch ):  
        old_branch = repo.active_branch
        repo.git.checkout( branch, b=branch.name )
        new_branch = repo.active_branch
        
        self.debug( "Changing branches: {} -> {}".format( old_branch, new_branch ) )

    # Get list of commits for the current branch
    def getCommits ( self, project, repo ):
        result = list( repo.iter_commits() )
        
        self.debug( "Retrieving {} commits from '{}'".format( len( result ), project ) )
        return result             

    # Return elements not already in an accumulating set
    def getUncheckedCommits ( new_commit, checked_commits ):
        return not new_commit in checked_commits

    # Return any keyword is within message
    def findKeywords ( keywords, message ):
        for keyword in keywords:
            if keyword in message:
                return True
        return False