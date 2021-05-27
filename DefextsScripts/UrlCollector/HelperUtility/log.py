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
    def clone(self):
        return self

    def print(self, message):
        prettify_string = self.PRETTIFY_MAP[VerboseLevel.MINIMAL]
        self.log("[{}] {}[MINIMAL] {}".format(datetime.datetime.now(), " " * prettify_string, message), VerboseLevel.INFO)

    def __init__(self, logLevel = VerboseLevel.INFO):
        self.LOG_LEVEL = logLevel
        self.prettifyLogOutput()
        
        assert not self.PRETTIFY_LOG_OUTPUT_SPACE is None, "Invalid value of {} for prettification ".format(self.PRETTIFY_LOG_OUTPUT_SPACE)
        assert ( type(self.PRETTIFY_LOG_OUTPUT_SPACE) is int and self.PRETTIFY_LOG_OUTPUT_SPACE > 0 )

        self.info("Initializing logging verbosity to {}".format(logLevel.name))

    def prettifyLogOutput(self):
        maxCharLength = 0

        for v in VerboseLevel:
            maxCharLength = max(maxCharLength, ( len(v.name) ))
        self.PRETTIFY_LOG_OUTPUT_SPACE = maxCharLength

        for v in VerboseLevel:
            self.PRETTIFY_MAP[v] = self.PRETTIFY_LOG_OUTPUT_SPACE - len(v.name)

    def info(self, message):
        prettify_string = self.PRETTIFY_MAP[VerboseLevel.INFO]

        self.log("[{}] {}[INFO] {}".format(datetime.datetime.now(), " " * prettify_string, message), VerboseLevel.INFO)

    def detailed(self, message):
        prettify_string = self.PRETTIFY_MAP[VerboseLevel.DETAILED]

        self.log("[{}] {}[DETAILED] {}".format(datetime.datetime.now(), " " * prettify_string, message), VerboseLevel.DETAILED)

    def debug(self, message):
        prettify_string = self.PRETTIFY_MAP[VerboseLevel.DEBUG]

        self.log("[{}] {}[DEBUG] {}".format(datetime.datetime.now(), " " * prettify_string, message), VerboseLevel.DEBUG)

    def warning(self, message):
        prettify_string = self.PRETTIFY_MAP[VerboseLevel.WARNING]

        self.log("[{}] {}[WARNING] {}".format(datetime.datetime.now(), " " * prettify_string, message), VerboseLevel.WARNING)

    def log(self, message, level):
        if self.LOG_LEVEL >= level:
            print(message)