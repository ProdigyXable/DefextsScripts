import threading
from HelperUtility.log import Log

class WorkerThread (threading.Thread):
    """Factory object for threads"""

    logger : Log = None
    ID = None

    def __init__(self, logger: Log, id, group = None, target = None, name = None, args = (), kwargs = None, *, daemon = None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.logger = logger
        self.ID = id
        self.logger.info("Created thread '{}'".format(self.getName()))
   
def testClass():
    l = Log()
    wt = WorkerThread(l, 1)

testClass()