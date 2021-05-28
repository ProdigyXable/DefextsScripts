import os
import CommitParser as parser
from HelperUtility.log import VerboseLevel

# --- Start --- #
configuration_details = "details.configuration"
if os.path.exists(configuration_details):
    cp = parser.CommitParser(VerboseLevel.DEBUG, configuration_details)
    cp.begin()
    cp.wait()
    cp.end()
else:
    print("Missing configuration file. Program exiting")