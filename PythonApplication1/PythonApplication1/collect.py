import UrlCollector as collector
import log
import getpass

# -- START --- #
github_username = input("Input your Github username (needed to increase the number of results):\t")
access_token = getpass.getpass("Input access token: \t")

LANGUAGES_CONFIGURATION = [ 'Kotlin', 'Scala', 'Groovy', 'Closure', 'Jython', 'JRuby', 'Java' ]

for language in LANGUAGES_CONFIGURATION:
    uc = collector.UrlCollector(log.Log.DEBUG, github_username, access_token)
    uc.begin(language)