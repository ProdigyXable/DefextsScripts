import UrlCollector.UrlCollector as collector
import os
import getpass

from HelperUtility.VerboseLevel import VerboseLevel

if __name__ == '__main__':

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

    LANGUAGE_CONFIGURATION = dict()
    
    LANGUAGE_CONFIGURATION[ 'Kotlin' ] = [ "Kotlin" ]
    LANGUAGE_CONFIGURATION[ 'Scala' ] = [ "Scala" ]
    LANGUAGE_CONFIGURATION[ 'Groovy' ] = [ "Groovy" ]
    LANGUAGE_CONFIGURATION[ 'Clojure' ] = [ "Clojure" ]
    
    # JRuby is grouped as Ruby by Github
    LANGUAGE_CONFIGURATION[ 'JRuby' ] = [ "Ruby", "Java" ]
    
    # Github does not report Jython as a language
    LANGUAGE_CONFIGURATION[ 'Jython' ] = [ "Python", "Java" ] 
    LANGUAGE_CONFIGURATION[ 'Java' ] = [ "Java" ]

    for language in LANGUAGE_CONFIGURATION.keys():
        uc = collector.UrlCollector( VerboseLevel.DEBUG, github_username, access_token )
        uc.begin( language, LANGUAGE_CONFIGURATION[ language ] )