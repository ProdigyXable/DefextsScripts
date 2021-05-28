from HelperUtility.log import Log

import git
import gc
import shutil

class CommitTask(object):
    """Class details to be changed later"""
    logger = None
    NAME = None
    TEMP_FOLDER_NAME = None
    REPO = None

    COUNT = 0

    def __init__(self, logger: Log):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = "T{}".format(CommitTask.COUNT)
        self.TEMP_FOLDER_NAME = "temp-{}".format(self.NAME)

        self.logger = logger

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
        
        self.downloadProject(project)
        self.getCommits(project)
        self.filterCommits(project)

        self.end()

    def end(self):
        gc.collect()
        self.REPO.git.clear_cache()
        git.rmtree(self.TEMP_FOLDER_NAME)

        self.detailed("Task has completed")

    def downloadProject(self, project):
        result = None
        self.debug("Downloading '{}'".format(project))
        
        self.REPO = git.Repo.clone_from(project, self.TEMP_FOLDER_NAME)
        commits = list(filter(lambda c: "zap" in c.message, self.REPO.iter_commits()))
        for commit in commits:
            print(commit)
        return result

    def getCommits(self, project):
        self.debug("Retrieving commits froms '{}'".format(project))

        result = None
        return result

    def filterCommits(self, project):
        self.debug("Filtering commits from '{}'".format(project))

        result = None
        return result