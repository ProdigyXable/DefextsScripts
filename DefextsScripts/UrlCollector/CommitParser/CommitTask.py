from HelperUtility.log import Log

import git
import gc
import shutil
import os

class CommitTask(object):
    """Class details to be changed later"""
    logger = None
    NAME = None

    TEMP_FOLDER_NAME = None

    KEYWORDS = None

    COUNT = 0

    def __init__(self, logger: Log, keywords):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = "T{}".format(CommitTask.COUNT)
        self.TEMP_FOLDER_NAME = "temp-{}".format(self.NAME)

        self.logger = logger
        self.KEYWORDS = keywords

    def info(self, message):
        self.logger.info("\t\t<{}> {}".format(self.NAME, message))

    def warning(self, message):
        self.logger.warning("\t\t<{}> {}".format(self.NAME, message))

    def detailed(self, message):
        self.logger.detailed("\t\t<{}> {}".format(self.NAME, message))

    def debug(self, message):
        self.logger.debug("\t\t<{}> {}".format(self.NAME, message))

    def print(self, message):
        self.logger.minimal("\t\t<{}> {}".format(self.NAME, message))

    def begin(self, project):
        self.detailed("Processing '{}'".format(project))  
        
        repo = self.downloadProject(project)
        commits = self.getCommits(project, repo)
        self.filterCommits(project, commits)

        self.end(repo)

    def end(self, repo):
        gc.collect()
        repo.git.clear_cache()
        git.rmtree(self.TEMP_FOLDER_NAME)

        self.detailed("Task has completed")

    def downloadProject(self, project):
        
        result = None
        self.debug("Downloading '{}'".format(project))
        
        if os.path.exists(self.TEMP_FOLDER_NAME):
            git.rmtree(self.TEMP_FOLDER_NAME)

        result = git.Repo.clone_from(project, self.TEMP_FOLDER_NAME)

        return result

    def getCommits(self, project, repo):
        self.debug("Retrieving commits from '{}'".format(project))

        result = None
        result = repo.iter_commits()
        return result

    def findKeywords(keywords, word):
        for keyword in keywords:
            if keyword in word:
                return True
        return False
               

    def filterCommits(self, project, commits):
        result = None
        self.debug("Filtering commits from '{}'".format(project))
        result = list(filter(lambda com: CommitTask.findKeywords( self.KEYWORDS, com.message), commits))
        
        for commit in result:
            print(commit, commit.message)
        return result