from HelperUtility.log import Log
from HelperUtility.ThreadManager import ThreadManager
from CommitTask import CommitTask

import os
import time

class CommitParser ( object ):
    """Class to parse all of a repository's commit, looking for those satisfying certain criteria"""

    CRITERIA_KEYWORDS = [ "fix", "add", "change", "modify", "remove", "error", "repair", "issue", "resolve", "solve" ]
    MAX_FILE_DIFF_LIMIT = 3
    MAX_LINES_CHANGED_PER_FILE = 4
    AVAILABLE_FILE_TYPES = None

    MAX_WORKER_THREADS = 4
    SLEEP_TIMER = 10

    URLS = []
    FUTURES = []

    OUTPUT_DIRECTORY = None
    DATASET_FILEPATH = None
    TEMP_FILEPATH = None

    logger = None
    tm = None

    def __init__ ( self, verbose, filepath ):
        self.logger = Log( verbose )
        self.logger.info( "Loading configuration details from {}".format( filepath ) )
        
        self.logger.info( "Creating thread executor size = {}".format( self.MAX_WORKER_THREADS ) )
        self.tm = ThreadManager( max_workers=self.MAX_WORKER_THREADS )

        for keyword in self.CRITERIA_KEYWORDS:
            self.logger.info( "Queried keyword: '{}'".format( keyword.lower() ) )

        self.constructFileTypes()

        # Read configuration file
        config_file = open( filepath, "r" )
        configuration_data = config_file.readlines()
        assert len( configuration_data ) >= 2, "Invalid content of {}".format( filepath )
        
        # Setup output directory
        self.OUTPUT_DIRECTORY = configuration_data[ 0 ].strip()
        os.makedirs( self.OUTPUT_DIRECTORY, exist_ok = True )
        self.logger.detailed( "Output directory = {}".format( self.OUTPUT_DIRECTORY ) )
        
        # Read primary input file
        self.DATASET_FILEPATH = configuration_data[ 1 ].strip()
        assert os.path.exists( self.DATASET_FILEPATH ), "Invalid input filepath specified: '{}'".format( self.DATASET_FILEPATH )
        self.logger.detailed( "Input filepath = {}".format( self.DATASET_FILEPATH ) )

    def begin ( self ):
        input_file = open( self.DATASET_FILEPATH, "r" )
        input_data = list( filter( lambda message: len( message.strip() ) > 0, input_file.readlines() ) )
        self.logger.info( "{} projects detected".format( len( input_data ) ) )
        
        # Send potential tasks to executor
        for project in input_data:
            project = project.strip()
            future = self.tm.submit( self.process, project )

            self.URLS.append( project )
            self.FUTURES.append( future )

    # Give progress updates as executor tasks complete
    def wait ( self ):
        total_tasks = len( self.FUTURES )
        unfinished_tasks_index_list = list( range( 0, total_tasks ) )
        problematic_tasks_index_list = []
        
        while len( unfinished_tasks_index_list ) > 0:
            finished_indexes = []

            time.sleep( self.SLEEP_TIMER ) # Sleep to prevent overconsumption of CPU resources

            # Iterate through tasks / futures
            for index in unfinished_tasks_index_list:
                future = self.FUTURES[ index ]
                
                # Has task completed in some fashion?
                if future.done():
                    finished_indexes.append( index )

                    # If an exception occurred, raise it
                    if not future.exception() is None:
                        problematic_tasks_index_list.append( index )
                        self.logger.warning( "Problematic project: {}".format( self.URLS[ index ] ) )
                        self.logger.debug( "\t{}".format( future.exception() ) )
                        raise future.exception() # Uncomment for testing /
                        # debug purposes.  Leave commented for release

            # Trim
            #  down list of uncompleted tasks
            unfinished_tasks_index_list = self.removedCompletedIndexes( unfinished_tasks_index_list, finished_indexes )
            current_tasks_left = len( unfinished_tasks_index_list )
            
            # Output executor task progress
            percent_completed = 50 * ( total_tasks - current_tasks_left ) / total_tasks
            completed_string = "=" * int( percent_completed )
            uncompleted_string = " " * ( 50 - int( percent_completed ) )

            self.logger.print( "[{:6.2f}%] [{}{}]".format( percent_completed, completed_string, uncompleted_string ) )
        self.logger.detailed( "{} problematic projects detected".format( len( problematic_tasks_index_list ) ) )
        
    def end ( self ):
        self.logger.info( "Shutting down thread executor" )
        self.tm.shutdown()
        self.tm = None

    def process ( self, project ):
        try:
            ct = CommitTask( self.logger, self.CRITERIA_KEYWORDS, self.AVAILABLE_FILE_TYPES, self.MAX_FILE_DIFF_LIMIT, self.MAX_LINES_CHANGED_PER_FILE )
            ct.begin( project )
        except Exception as e:
            # self.logger.warning("{} {}".format(type(e), e))
            raise e

    def constructFileTypes ( self ):
        ft = set()
        ft.update( [ "java", "kt", "kts", "ktm" ] )
        ft.update( [ "java", "scala", "sc" ] )
        ft.update( [ "java", "groovy", "gvy", "gy", "gsh" ] )
        ft.update( [ "java", "clj", "cljs", "cljc", "edn" ] )
        ft.update( [ "java", "py" ] )
        ft.update( [ "java", "rb" ] )
        ft.update( [ "java" ] )

        self.AVAILABLE_FILE_TYPES = ft

    def removedCompletedIndexes ( self, unfinished, finished ):
        for item in finished:
            unfinished.remove( item )
        return unfinished