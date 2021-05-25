import UrlCollector as collector
from log import VerboseLevel
import os
import getpass

# -- START --- #
access_file = open("details.access", "r")
if( os.path.exists(access_file.name) ):
    details = access_file.readlines()
    assert  len(details) == 2, "Invalid access content"
    github_username = details[0].strip()
    access_token = details[1].strip()
else:
    github_username = input("Input your Github username (needed to increase the number of results):\t").strip()
    access_token = getpass.getpass("Input access token: \t").strip()

LANGUAGES_CONFIGURATION = [ 'Kotlin', 'Scala', 'Groovy', 'Closure', 'Jython', 'JRuby', 'Java' ]

for language in LANGUAGES_CONFIGURATION:
    uc = collector.UrlCollector(VerboseLevel.DEBUG, github_username, access_token)
    uc.begin(language)