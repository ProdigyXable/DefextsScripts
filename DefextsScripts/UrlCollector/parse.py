import os
import CommitParser

from HelperUtility.VerboseLevel import VerboseLevel

    # --- Start --- #
if __name__ == '__main__':
    configuration_details = "details.configuration"
    if os.path.exists( configuration_details ):
        cp = CommitParser.CommitParser( VerboseLevel.DEBUG, configuration_details )
        cp.begin()
        cp.wait()
        cp.end()
    else:
        print( "Missing configuration file. Program exiting" )