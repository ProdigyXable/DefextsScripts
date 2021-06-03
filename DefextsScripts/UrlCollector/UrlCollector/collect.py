from HelperUtility.VerboseLevel import VerboseLevel

import UrlCollector as collector
import os
import getpass

# -- START --- #
access_file_name = "details.access"

if( os.path.exists( access_file_name ) ):
    access_file = open( access_file_name, "r" )
    details = access_file.readlines()
    assert  len( details ) == 2, "Invalid access content"
    github_username = details[ 0 ].strip()
    access_token = details[ 1 ].strip()
else:
    github_username = input( "Input your Github username (authenticated users may request more per minute): \t" ).strip()
    access_token = getpass.getpass( "Input password / access token: \t" ).strip()

LANGUAGES_CONFIGURATION = [ 'Kotlin', 'Scala', 'Groovy', 'Clojure', 'Jython', 'JRuby', 'Java' ]

for language in LANGUAGES_CONFIGURATION:
    uc = collector.UrlCollector( VerboseLevel.DEBUG, github_username, access_token )
    uc.begin( language )