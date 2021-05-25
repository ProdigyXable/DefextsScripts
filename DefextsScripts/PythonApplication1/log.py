import datetime
import enum

class VerboseLevel (enum.IntEnum):
    MINIMAL = -1
    INFO = 1
    WARNING = 10
    DETAILED = 100
    DEBUG = 1000

class Log (object):

    """Logging utility class"""
    
    # LOG LEVEL

    PRETTIFY_LOG_OUTPUT_SPACE = None
    PRETTIFY_MAP = {}

    def print(self, message):
        self.log(message, VerboseLevel.MINIMAL)

    def __init__(self, logLevel):
        self.LOG_LEVEL = logLevel
        self.prettifyLogOutput()
        
        assert not self.PRETTIFY_LOG_OUTPUT_SPACE is None, "Invalid value of {} for prettification ".format(self.PRETTIFY_LOG_OUTPUT_SPACE)
        assert ( type(self.PRETTIFY_LOG_OUTPUT_SPACE) is int and self.PRETTIFY_LOG_OUTPUT_SPACE > 0 )

        self.info("Setting logging verbosity to {}".format(logLevel.name))

    def prettifyLogOutput(self):
        maxCharLength = 0

        for v in VerboseLevel:
            maxCharLength = max(maxCharLength, ( len(v.name) ))
        self.PRETTIFY_LOG_OUTPUT_SPACE = maxCharLength

        for v in VerboseLevel:
            self.PRETTIFY_MAP[v] = self.PRETTIFY_LOG_OUTPUT_SPACE - len(v.name)

    def info(self, message):
        forced_append = self.PRETTIFY_MAP[VerboseLevel.INFO]

        self.log("[{}] {}[INFO] {}".format(datetime.datetime.now(), " " * forced_append, message), VerboseLevel.INFO)

    def detailed(self, message):
        forced_append = self.PRETTIFY_MAP[VerboseLevel.DETAILED]

        self.log("[{}] {}[DETAILED] {}".format(datetime.datetime.now(), " " * forced_append, message), VerboseLevel.DETAILED)

    def debug(self, message):
        forced_append = self.PRETTIFY_MAP[VerboseLevel.DEBUG]

        self.log("[{}] {}[DEBUG] {}".format(datetime.datetime.now(), " " * forced_append, message), VerboseLevel.DEBUG)

    def warning(self, message):
        forced_append = self.PRETTIFY_MAP[VerboseLevel.Warning]

        self.log("[{}] {}[WARNING] {}".format(datetime.datetime.now(), " " * forced_append, message), VerboseLevel.WARNING)

    def log(self, message, level):
        if self.LOG_LEVEL >= level:
            print(message)