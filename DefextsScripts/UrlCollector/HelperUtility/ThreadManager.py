import HelperUtility

class ThreadManager (object):
    """description of class"""

    MAX_THREADS = 1
    THREAD_LIST = []
    def __init__(self, logger, maxThreads):
        self.MAX_THREADS = maxThreads

        for i in range(0, self.MAX_THREADS):
            thread = HelperUtility.WorkerThread.WorkerThread(logger, i)
            self.THREAD_LIST.append(thread)

def testClass():
    tm = ThreadManager(None, 2)

testClass()