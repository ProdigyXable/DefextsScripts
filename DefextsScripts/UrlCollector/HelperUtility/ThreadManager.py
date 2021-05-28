import concurrent.futures
from HelperUtility.log import Log

class ThreadManager(concurrent.futures.ThreadPoolExecutor):
    """"Class information to be changed"""

    def __init__(self, max_workers = None):
        return super().__init__(max_workers)