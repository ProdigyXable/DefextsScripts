import datetime

class Log (object):

    """Logging utility class"""
    
    # LOG LEVEL
    
    LOG_LEVEL = 0

    INFO = 1
    WARNING = 10
    DETAILED = 100
    DEBUG = 1000

    def print(self, message):
        self.log(message, -1)

    def __init__(self, logLevel):
        self.LOG_LEVEL = logLevel
        print("Logging utility set to {}".format(self.LOG_LEVEL))

    def info(self, message):
        self.log("[{}] [INFO] {}".format(datetime.datetime.now(), message), self.INFO)

    def detailed(self, message):
        self.log("[{}] [DETAILED] {}".format(datetime.datetime.now(), message), self.DETAILED)

    def debug(self, message):
        self.log("[{}] [DEBUG] {}".format(datetime.datetime.now(), message), self.DEBUG)

    def warning(self, message):
        self.log("[{}] [WARNING] {}".format(datetime.datetime.now(), message), self.WARNING)

    def log(self, message, level):
        if self.LOG_LEVEL >= level:
            print(message)