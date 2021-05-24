
import requests
import time
import os
import getpass
import math
import log
import datetime

class UrlCollector (object):

    """Crawls Github for a given progrmaming languages and retrieves all public repositories created between two date ranges"""
    # LOG
    logging = None

    # Github Details
    GITHUB_USERNAME = None
    ACCESS_TOKEN = None
    GITHUB_ACCESS_TUPLE = None

    # Github API Settings
    GITHUB_MAX_INDEX = 1000
    MAX_RESULTS_PER_PAGE = 100
    MAX_PAGE_NUMBER = int(GITHUB_MAX_INDEX / MAX_RESULTS_PER_PAGE)

    LANGUAGE = None
    SKIPPED_DAYS = 0
    MINIMUM_SKIPPED_DAYS = 0

    # START POINT CONFIGURATION
    INITIAL_ISO_YEAR = 2021
    INITIAL_ISO_MONTH = 5
    INITIAL_ISO_DAY = 21

    # END POINT CONFIGURATION
    STOP_YEAR = 2009

    # TIMEOUT
    SLEEP_TIMEOUT = 3

    # Other
    STRING_REPEAT_CONSTANT = 24

    # Constructor
    def __init__(self, logLevel, github_username, access_token):
        assert self.SKIPPED_DAYS >= self.MINIMUM_SKIPPED_DAYS, "Number of skipped days must be at least 0" 
        
        self.GITHUB_USERNAME = github_username
        assert not self.GITHUB_USERNAME is None, "Username must not be {}".format(None)
        
        self.ACCESS_TOKEN = access_token
        assert not self.ACCESS_TOKEN is None, "Access token must not be {}".format(None)

        self.GITHUB_ACCESS_TUPLE = ( self.GITHUB_USERNAME, self.ACCESS_TOKEN )
        self.logging = log.Log(logLevel)

        # Request data from Github server
    def request(self, url, github_account):
        self.logging.debug("Checking url {}".format(url))
        result = requests.get(url, auth=( github_account )).json()

        time.sleep(self.SLEEP_TIMEOUT) # Timeout after each request to prevent api overload
        return result

    def get_num(self, url):
        total_num = 0
        json_data = self.request(url, self.GITHUB_ACCESS_TUPLE)

        if( not ( "total_count" ) in json_data ):
            self.logging.warning("Request failure: {}".format(json_data["message"]))
        else:
            total_num = json_data["total_count"]
            self.logging.info("[{}] projects found for {}".format(total_num, url))

        return total_num

    def writedata(self, repo_dicts, i, file):
        
        repo_dicti = repo_dicts[i]
        file.writelines("{} {} {}\n".format(repo_dicti['stargazers_count'], repo_dicti['clone_url'], repo_dicti['forks_count']))

    def collect_data(self, base_url, total_num, outputFile):
        num = int(total_num / self.MAX_RESULTS_PER_PAGE) + 1

        # Iterate through each page in accessible output
        max_pages_needed = 1 + min(num, self.MAX_PAGE_NUMBER + 1)
        for pageNum_index in range(1, max_pages_needed):

            # Update url to include page information
            url = "{}&page={}".format(base_url, pageNum_index)
            self.logging.info("Fetching page: {}".format(pageNum_index))
            data = self.request(url, self.GITHUB_ACCESS_TUPLE)
        
            if( "items" in data ):
                date_response_index = 0
                repo_dicts = data['items']
                data_response_length = len(repo_dicts)
                            
                while( date_response_index < data_response_length ):
                    self.writedata(repo_dicts, date_response_index, outputFile) 
                    date_response_index += 1

                outputFile.flush()
                self.logging.debug("\t - Saved {} entries".format(data_response_length))
            else:
                self.logging.warning("Request failure: {}".format(data["message"]))
                time.sleep(self.SLEEP_TIMEOUT * 3) # Extra timeout, in case too many api events are being called
        self.logging.info("-" * self.STRING_REPEAT_CONSTANT)

    def crawl(self, outputFile):          
        self.logging.info("Processing urls for {}".format(self.LANGUAGE))
        self.logging.info("-" * self.STRING_REPEAT_CONSTANT)
               
        # Set original date range
        NewIsoDate = self.decrementDate(self.INITIAL_ISO_YEAR, self.INITIAL_ISO_MONTH, self.INITIAL_ISO_DAY, 0)
        OldIsoDate = NewIsoDate
        self.logging.detailed("Constructing initial date range starting from {}".format(OldIsoDate))
        
        # Loop from startDate to endDate
        while( NewIsoDate[0] >= self.STOP_YEAR ):
            
            # Decrement date range
            OldIsoDate = self.decrementDate(NewIsoDate[0], NewIsoDate[1], NewIsoDate[2], 1)
            NewIsoDate = self.calculateNewIsoDate(OldIsoDate)

            # Construct api url from known parameters
            url = "https://api.github.com/search/repositories?q=language:{}+created:{}..{}&per_page={}" \
                .format(self.LANGUAGE, \
                self.calculateIsoDateString(NewIsoDate), \
                self.calculateIsoDateString(OldIsoDate), \
                self.MAX_RESULTS_PER_PAGE)
        
            total_num = self.get_num(url)

            if ( total_num > 0 ):
                self.collect_data(url, total_num, outputFile)
            if ( total_num > self.GITHUB_MAX_INDEX ):
                self.logging.debug("{}+ urls detected. {} skipped".format(self.GITHUB_MAX_INDEX, total_num - self.GITHUB_MAX_INDEX))

    # Program entry point and opening processes
    def begin(self, language):
        
        self.LANGUAGE = language
        assert not self.LANGUAGE is None, "Language must not be {} -> {}".format(None, self.LANGUAGE)

        configuration = []
        configuration.append("Language = {}".format(self.LANGUAGE))
        configuration.append("Range = {} - {}".format(self.calculateIsoDateString(( self.INITIAL_ISO_YEAR, self.INITIAL_ISO_MONTH, self.INITIAL_ISO_DAY )), self.STOP_YEAR))
        configuration.append("Skipped days = {}".format(self.SKIPPED_DAYS))
        configuration.append("Sleep timeout = {}".format(self.SLEEP_TIMEOUT))
        configuration.append("Start = {}".format(datetime.datetime.now()))

        configuration_file = open("{}.configuration".format(self.LANGUAGE), "w")
        for parameter in configuration:
            self.logging.info(parameter)
            configuration_file.write("{}\n".format(parameter))
        configuration_file.flush()

        outputFile = open("{}.output".format(self.LANGUAGE), "a")
        outputFile.truncate(0)
        # Brief file manipulation [END] #

        self.crawl(outputFile)
        
        configuration_file("End = {}".format(datetime.datetime.now()))
        
        configuration_file.close()
        outputFile.close()

        self.end()

    # Program termination point and closing processes
    def end(self):
        self.logging.info("Program ending")
        self.logging.info("-" * self.STRING_REPEAT_CONSTANT)

    # Decrements date tuple
    def decrementDate(self, year, month, day, decrement):
        assert month >= 0 and month <= 12, "Invalid month specification" 
        assert day >= 0 and day <= 31, "Invalid date specification" 

        newYear = year
        newMonth = month
        newDay = day

        if( newDay > 1 ):
            newDay = max(newDay - decrement, 1)
        elif( newDay <= 1 ):
            if( newMonth > 1 ):
                newMonth -= 1
                newDay = maxDays(newMonth)
            else:
                newMonth = 12
                newDay = maxDays(newMonth)
                newYear -= 1

        self.logging.debug("Updated date range {}-{}-{} -> {}-{}-{}".format(day, month, year, newDay, newMonth, newYear))

        assert newMonth >= 0 and newMonth <= 12, "Invalid month value" 
        assert newDay >= 0 and newDay <= 31, "Invalid date value" 

        return ( newYear, newMonth, newDay )

    # Minor optimization to avoid unneccessary decrements
    def calculateNewIsoDate(self, OldIsoDate):
        result = None

        if( self.SKIPPED_DAYS > 0 ):
            result = self.decrementDate(OldIsoDate[0], OldIsoDate[1], OldIsoDate[2], self.SKIPPED_DAYS)
            self.logging.detailed("Decrementing date from {} to {}".format(OldIsoDate, result))
        else:
            result = OldIsoDate      
            self.logging.detailed("Setting date range to {} - {}".format(OldIsoDate, result))

        return result

    # Determine may days in a month
    def maxDays(self, month):
        assert month > 0 and month <= 12, "Invalid month specification" 

        result = None
        if( month == 2 ):
            result = 28
        elif( month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12 ):
            result = 31
        else:
            result = 30

        self.logging.debug("Max days for month {} is {}".format(month, result))

        assert not result is None, "Invalid month result" 
        return result

    def calculateIsoDateString(self, isoDate):
        year = isoDate[0]
        month = isoDate[1]
        day = isoDate[2]

        monthString = ( "0{}".format(month) )[-2:]
        dayString = ( "0{}".format(day) )[-2:]

        result = "{}-{}-{}".format(year, monthString, dayString) 
        self.logging.debug("ISO DATE for {} is {}".format(isoDate, result))
        return ( result )

# -- START --- #
github_username = input("Input your Github username (needed to increase the number of results):\t")
access_token = getpass.getpass("Input access token: \t")

for language in [ 'Kotlin', 'Scala', 'Groovy', 'Closure', 'Jython', 'JRuby', 'Java' ]:
    uc = UrlCollector(log.Log.DEBUG, github_username, access_token)
    uc.begin(language)