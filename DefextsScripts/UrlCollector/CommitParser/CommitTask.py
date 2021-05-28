from HelperUtility.log import Log

class CommitTask(object):
    """Class details to be changed later"""
    logger = None
    NAME = None

    COUNT = 0

    def __init__(self, logger: Log):
        CommitTask.COUNT = CommitTask.COUNT + 1
        self.NAME = CommitTask.COUNT
        self.logger = logger

    def info(self, message):
        self.logger.info("\t\t<T_{}> {}".format(self.NAME, message))

    def warning(self, message):
        self.logger.warning("\t\t<T_{}> {}".format(self.NAME, message))

    def detailed(self, message):
        self.logger.detailed("\t\t<T_{}> {}".format(self.NAME, message))

    def debug(self, message):
        self.logger.debug("\t\t<T_{}> {}".format(self.NAME, message))

    def print(self, message):
        self.logger.minimal("\t\t<T_{}> {}".format(self.NAME, message))

    def begin(self, project):
        self.detailed("Processing '{}'".format(project))  
        
        self.downloadProject(project)
        self.getCommits(project)
        self.filterCommits(project)

        self.end()

    def end(self):
        self.detailed("Task has completed")

    def downloadProject(self, project):
        self.debug("Downloading '{}'".format(project))

        result = None
        return result

    def getCommits(self, project):
        self.debug("Retrieving commits froms '{}'".format(project))

        result = None
        return result

    def filterCommits(self, project):
        self.debug("Filtering commits from '{}'".format(project))

        result = None
        return result