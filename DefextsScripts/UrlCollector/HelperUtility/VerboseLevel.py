import enum

class VerboseLevel ( enum.IntEnum ):
    MINIMAL = -1
    INFO = 1
    WARNING = 10
    DETAILED = 100
    DEBUG = 1000