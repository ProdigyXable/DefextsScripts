import os
import time

from HelperUtility.Log import Log
from HelperUtility.ThreadManager import ThreadManager
from CommitTask import CommitTask

class CommitParser ( object ):
    """Class to parse all of a repository's commit, looking for those satisfying certain criteria"""

    CRITERIA_KEYWORDS = [ "fix", "add", "change", "modify", "remove", "error", "repair", "issue", "resolve", "solve" ]
    ACCEPTABLE_BUILD_SYSTEM_FILES = None
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
        self.setAcceptableBuildSystems()

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

            future = self.tm.submit( CommitParser.process, \
               project, \
               self.logger, \
               self.CRITERIA_KEYWORDS, \
               self.AVAILABLE_FILE_TYPES, \
               self.MAX_FILE_DIFF_LIMIT, \
               self.MAX_LINES_CHANGED_PER_FILE, \
               self.ACCEPTABLE_BUILD_SYSTEM_FILES )

            self.URLS.append( project )
            self.FUTURES.append( future )

    # Give progress updates as executor tasks complete
    def wait ( self ):
        total_tasks = len( self.FUTURES )
        unfinished_tasks_index_list = list( range( 0, total_tasks ) )
        problematic_tasks_index_list = []
        
        output_file = open( "{}{}successful_commits.output".format( self.OUTPUT_DIRECTORY, os.path.sep ), "w" )
        exception_file = open( "{}{}error_projects.output".format( self.OUTPUT_DIRECTORY, os.path.sep ), "w" )
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
                    if future.exception() is None:
                        project, results = future.result() 
                        self.saveSuccessfulResults( project, results, output_file )
                    else:
                        problematic_tasks_index_list.append( index )
                        self.logger.warning( "Problematic project: {}".format( self.URLS[ index ] ) )
                        self.logger.debug( "\t{}".format( future.exception() ) )
                        self.saveExceptionResults( self.URLS[ index ], future.exception(), exception_file )
                        raise future.exception() # Uncomment for testing /
                        # debug purposes.  Leave commented for release

            # Trimdown list of uncompleted tasks
            unfinished_tasks_index_list = self.removedCompletedIndexes( unfinished_tasks_index_list, finished_indexes )
            current_tasks_left = len( unfinished_tasks_index_list )
            
            # Output executor task progress
            percent_completed = 100 * ( total_tasks - current_tasks_left ) / total_tasks
            completed_string = "=" * int( percent_completed )
            uncompleted_string = " " * ( 100 - int( percent_completed ) )

            self.logger.print( "[{:6.2f}%] [{}{}]".format( percent_completed, completed_string, uncompleted_string ) )
        self.logger.detailed( "{} problematic projects detected".format( len( problematic_tasks_index_list ) ) )
        
    def end ( self ):
        self.logger.info( "Shutting down thread executor" )
        self.tm.shutdown()
        self.tm = None

    def saveSuccessfulResults ( self, project, future_results, file ):
        file.write( "{}\n".format( project ) )

        for commit in future_results:
            file.write( "\t{}\n".format( commit ) )
        file.flush()

    def saveExceptionResults ( self, project, future_exception, file ):
        
        file.write( "Error = [{}]\n".format( project ) )
        file.write( "{}\n".format( future_exception ) )
        file.write( "----------------\n" )
        file.flush()

    def process ( project, log, keywords, filetypes, diff_limit, file_line_changes, build_system_files ):
        try:
            ct = CommitTask( log, keywords, filetypes, diff_limit, file_line_changes, build_system_files )
            project, commits = ct.begin( project )
            return project, commits
        except Exception as e:
            # self.logger.warning("{} {}".format(type(e), e))
            raise e

    def setAcceptableBuildSystems ( self ):
        bs = set()
        bs.update( [ "pom.xml" ] ) # Maven "required" files
        bs.update( [ "build.gradle" ] ) # Groovy "required" files

        self.ACCEPTABLE_BUILD_SYSTEM_FILES = bs

    def constructFileTypes ( self ):
        ft = set()
        ft.update( [ "java", "kt", "kts", "ktm" ] ) # Kotlin-based files
        ft.update( [ "java", "scala", "sc" ] ) # Scala-based files
        ft.update( [ "java", "groovy", "gvy", "gy", "gsh" ] ) # Groovy-based files
        ft.update( [ "java", "clj", "cljs", "cljc", "edn" ] ) # Clojure-based files
        ft.update( [ "java", "py" ] ) # Jython/Python-based files
        ft.update( [ "java", "rb" ] ) # JRuby/Ruby-based files
        ft.update( [ "java" ] ) # Java-based files

        self.AVAILABLE_FILE_TYPES = ft

    def removedCompletedIndexes ( self, unfinished, finished ):
        for item in finished:
            unfinished.remove( item )
        return unfinished