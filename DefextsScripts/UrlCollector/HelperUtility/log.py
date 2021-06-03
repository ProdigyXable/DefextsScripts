import datetime

from HelperUtility.VerboseLevel import VerboseLevel

class Log ( object ):

    """Logging utility class"""
   
    # LOG LEVEL
    LOG_LEVEL = None

    PRETTIFY_LOG_OUTPUT_SPACE = None
    PRETTIFY_MAP = None
    
    def clone ( self ):
        return self

    def print ( self, message ):
        prettify_string = self.PRETTIFY_MAP[ VerboseLevel.MINIMAL ]
        self.log( "[{}] {}[MINIMAL] {}".format( datetime.datetime.now(), " " * prettify_string, message ), VerboseLevel.INFO )

    def __init__ ( self, logLevel = VerboseLevel.INFO ):
        self.LOG_LEVEL = logLevel
        
        self.setupLogOutputPrettification()
        
        assert not self.PRETTIFY_LOG_OUTPUT_SPACE is None, "Invalid value of {} for prettification ".format( self.PRETTIFY_LOG_OUTPUT_SPACE )
        assert ( type( self.PRETTIFY_LOG_OUTPUT_SPACE ) is int and self.PRETTIFY_LOG_OUTPUT_SPACE > 0 )

        self.info( "Initializing logging verbosity to {}".format( logLevel.name ) )

    def setupLogOutputPrettification ( self ):
        maxCharLength = 0

        self.PRETTIFY_MAP = {}

        # Iterate to get max distance
        for v in VerboseLevel:
            maxCharLength = max( maxCharLength, ( len( v.name ) ) )
        self.PRETTIFY_LOG_OUTPUT_SPACE = maxCharLength

        # Iterate again to fill in data structure
        for v in VerboseLevel:
            self.PRETTIFY_MAP[ v ] = self.PRETTIFY_LOG_OUTPUT_SPACE - len( v.name )

    def info ( self, message ):
        prettify_string = self.PRETTIFY_MAP[ VerboseLevel.INFO ]

        self.log( "[{}] {}[INFO] {}".format( datetime.datetime.now(), " " * prettify_string, message ), VerboseLevel.INFO )

    def detailed ( self, message ):
        prettify_string = self.PRETTIFY_MAP[ VerboseLevel.DETAILED ]

        self.log( "[{}] {}[DETAILED] {}".format( datetime.datetime.now(), " " * prettify_string, message ), VerboseLevel.DETAILED )

    def debug ( self, message ):
        prettify_string = self.PRETTIFY_MAP[ VerboseLevel.DEBUG ]

        self.log( "[{}] {}[DEBUG] {}".format( datetime.datetime.now(), " " * prettify_string, message ), VerboseLevel.DEBUG )

    def warning ( self, message ):
        prettify_string = self.PRETTIFY_MAP[ VerboseLevel.WARNING ]

        self.log( "[{}] {}[WARNING] {}".format( datetime.datetime.now(), " " * prettify_string, message ), VerboseLevel.WARNING )

    def log ( self, message, level ):
        if self.LOG_LEVEL >= level:
            print( message )