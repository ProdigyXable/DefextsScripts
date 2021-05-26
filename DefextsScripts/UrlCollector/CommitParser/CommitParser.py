from HelperUtility.log import Log

class CommitParser (object):
    """Class to parse all of a repository's commit, looking for those satisfying certain criteria"""

    CRITERIA_KEYWORDS = [ "fix", "remove", "error", "repair", "issue", "resolve", "solve" ]
    
    THREADS = 2

    logger = None

    def __init__(self, verbose, filepath):
        self.logger = Log(verbose)
        self.logger.info("Loading configuration details from {}".format(filepath))


    def begin(self):
        pass