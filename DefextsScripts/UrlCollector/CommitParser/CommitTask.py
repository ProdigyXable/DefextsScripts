from HelperUtility.log import Log

import git
import gc
import shutil
import os

class CommitTask ( object ):
    """Class details to be changed later"""
    logger = None

    TEMP_FOLDER_NAME = None # Path of temp folder used to hold repository

    KEYWORDS = None # List of keywords to be searched for within individual commits

    COUNT = 0 # Used to determine the 'name' of the thread
    NAME = None

    def __init__ ( self, logger: Log, keywords ):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = "T{}".format( CommitTask.COUNT )
        self.TEMP_FOLDER_NAME = "temp-{}".format( self.NAME )

        self.logger = logger
        self.KEYWORDS = keywords

    # --- LOGGER HELPER METHODS [START] --- #
    def info ( self, message ):
        if logger is None:
            return

        self.logger.info( "\t\t<{}> {}".format( self.NAME, message ) )

    def warning ( self, message ):
        if logger is None:
            return

        self.logger.warning( "\t\t<{}> {}".format( self.NAME, message ) )

    def detailed ( self, message ):
        if logger is None:
            return

        self.logger.detailed( "\t\t<{}> {}".format( self.NAME, message ) )

    def debug ( self, message ):
        if logger is None:
            return

        self.logger.debug( "\t\t<{}> {}".format( self.NAME, message ) )

    def print ( self, message ):
        if logger is None:
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
            self.checkoutBranch( project, original_repo, branch )
            
            commits = self.getCommits( project, original_repo )

            filtered_commits = self.filterCommitsOnKeywords( project, commits, checked_commits )
            checked_commits.update( commits )

            satisfactory_commits.update( filtered_commits )

            self.debug( "{} commits currently accmulated".format( len( satisfactory_commits ) ) )

        self.info( "{} unique satisfactory commits found from {} branches".format( len( satisfactory_commits ), len( branches ) ) )

        self.end( original_repo )
        return ( project, satisfactory_commits )

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
    def checkoutBranch ( self, project, repo, branch ):  
        old_branch = repo.active_branch
        repo.git.checkout( branch, b=branch.name )
        new_branch = repo.active_branch
        
        self.debug( "Changing branches: {} -> {}".format( old_branch, new_branch ) )

    # Get list of commits for the current branch
    def getCommits ( self, project, repo ):
        result = list( repo.iter_commits() )
        
        self.debug( "Retrieving {} commits from '{}'".format( len( result ), project ) )
        return result             

    def filterCommitsOnKeywords ( self, project, commits, already_checked_commits ):
        # For efficiency, only checked commits we have not already looked at
        unchecked_commits = list( filter( lambda com: CommitTask.getUncheckedCommits( com, already_checked_commits ), commits ) )
        
        # Return only commits containing any queried keywords
        result = list( filter( lambda new_commit: CommitTask.findKeywords( self.KEYWORDS, new_commit.message ), unchecked_commits ) )
        
        self.detailed( "{} / {} new commits successfully filtered + collected".format( len( result ), len( unchecked_commits ) ) )
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