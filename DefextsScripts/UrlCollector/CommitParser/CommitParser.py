from HelperUtility.log import Log
from HelperUtility.ThreadManager import ThreadManager
from CommitTask import CommitTask

import os
import time

class CommitParser (object):
    """Class to parse all of a repository's commit, looking for those satisfying certain criteria"""

    CRITERIA_KEYWORDS = [ "fix", "add", "change", "modify", "remove", "error", "repair", "issue", "resolve", "solve" ]
    
    MAX_WORKER_THREADS = 4
    SLEEP_TIMER = 1

    URLS = []
    FUTURES = []

    OUTPUT_DIRECTORY = None
    DATASET_FILEPATH = None
    TEMP_FILEPATH = None

    logger = None
    tm = None

    def __init__(self, verbose, filepath):
        self.logger = Log(verbose)
        self.logger.info("Loading configuration details from {}".format(filepath))
        
        self.logger.info("Creating thread executor size = {}".format(self.MAX_WORKER_THREADS))
        self.tm = ThreadManager(max_workers=self.MAX_WORKER_THREADS)

        for keyword in self.CRITERIA_KEYWORDS:
            self.logger.info("Queried keyword: '{}'".format(keyword.lower()))

        # Read configuration file
        config_file = open(filepath, "r")
        configuration_data = config_file.readlines()
        assert len(configuration_data) >= 2, "Invalid content of {}".format(filepath)
        
        # Setup output directory
        self.OUTPUT_DIRECTORY = configuration_data[0].strip()
        os.makedirs(self.OUTPUT_DIRECTORY, exist_ok = True)
        self.logger.detailed("Output directory = {}".format(self.OUTPUT_DIRECTORY))
        
        # Read primary input file
        self.DATASET_FILEPATH = configuration_data[1].strip()
        assert os.path.exists(self.DATASET_FILEPATH), "Invalid input filepath specified: '{}'".format(self.DATASET_FILEPATH)
        self.logger.detailed("Input filepath = {}".format(self.DATASET_FILEPATH))

    def begin(self):
        input_file = open(self.DATASET_FILEPATH, "r")
        input_data = input_file.readlines()
        self.logger.info("{} projects detected".format(len(input_data)))
        
        # Send potential tasks to executor
        for project in input_data:
            project = project.strip()
            future = self.tm.submit(self.process, project)

            self.URLS.append(project)
            self.FUTURES.append(future)

    # Give progress updates as executor tasks complete
    def wait(self):
        total_tasks = len(self.FUTURES)
        unfinished_indexes = list(range(0, total_tasks))
        problematic_indexes = []
        
        while len(unfinished_indexes) > 0:
            finished_indexes = []

            time.sleep(self.SLEEP_TIMER) # Sleep to prevent overconsumption of CPU resources

            # Iterate through tasks / futures
            for index in unfinished_indexes:
                
                future = self.FUTURES[index]
                
                # Has task completed in some fashion?
                if future.done():
                    finished_indexes.append(index)
                    if not future.exception() is None:
                        problematic_indexes.append(index)
                        self.logger.warning("Problematic project: {}".format(self.URLS[index]))
                        self.logger.debug("\t{}".format(future.exception()))

            unfinished_indexes = self.removedCompletedIndexes(unfinished_indexes, finished_indexes)
            current_tasks = len(unfinished_indexes)
            
            # Output executor task progress
            percent_completed = 100 * (total_tasks - current_tasks) / total_tasks
            completed_string = "=" * int(percent_completed)
            uncompleted_string = " " * (100 - int(percent_completed))

            self.logger.print("[{:6.2f}%] [{}{}]".format(percent_completed, completed_string, uncompleted_string))
        self.logger.detailed("{} problematic projects detected".format(len(problematic_indexes)))
        
    def end(self):
        self.logger.info("Shutting down thread executor")
        self.tm.shutdown()
        self.tm = None

    def process(self, project):
        try:
            ct = CommitTask(self.logger, self.CRITERIA_KEYWORDS)
            ct.begin(project)
        except Exception as e:
            # self.logger.warning("{} {}".format(type(e), e))
            raise e

    def removedCompletedIndexes(self, unfinished, finished):
        for item in finished:
            unfinished.remove(item)
        return unfinished