from HelperUtility.log import Log
import os

class CommitParser (object):
    """Class to parse all of a repository's commit, looking for those satisfying certain criteria"""

    CRITERIA_KEYWORDS = [ "fix", "add", "change", "modify" "remove", "error", "repair", "issue", "resolve", "solve" ]
    
    THREADS = 2

    OUTPUT_DIRECTORY = None
    DATASET_FILEPATH = None
    TEMP_FILEPATH = None

    logger = None

    def __init__(self, verbose, filepath):
        self.logger = Log(verbose)
        self.logger.info("Loading configuration details from {}".format(filepath))
        
        for keyword in self.CRITERIA_KEYWORDS:
            self.logger.info("Queried keyword: {}".format(keyword.lower()))

        config_file = open(filepath, "r")
        configuration_data = config_file.readlines()
        assert len(configuration_data) >= 2, "Invalid content of {}".format(filepath)
        
        self.OUTPUT_DIRECTORY = configuration_data[0].strip()
        os.makedirs(self.OUTPUT_DIRECTORY, exist_ok = True)
        self.logger.detailed("Output directory = {}".format(self.OUTPUT_DIRECTORY))
        
        self.DATASET_FILEPATH = configuration_data[1].strip()
        assert os.path.exists(self.DATASET_FILEPATH), "Invalid input filepath specified: {}".format(self.DATASET_FILEPATH)
        self.logger.detailed("Input filepath = {}".format(self.DATASET_FILEPATH))

    def begin(self):
        input_file = open(self.DATASET_FILEPATH, "r")
        input_data = input_file.readlines()
        self.logger.info("{} projects detected".format(len(input_data)))