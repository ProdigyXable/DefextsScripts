import os
from CommitParser import CommitParser
from HelperUtility.log import VerboseLevel

# --- Start --- #
configuration_details = "details.configuration"
if os.path.exists(configuration_details):
    cp = CommitParser(VerboseLevel.DEBUG, configuration_details)
    cp.begin()
    cp.wait()
    cp.end()
else:
    print("Missing configuration file. Program exiting")