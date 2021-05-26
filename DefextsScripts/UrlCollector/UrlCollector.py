import requests
import time
import os
import math
from log import Log
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
        self.logging = Log(logLevel)

    # Request data from Github server
    def request(self, url, github_account):
        self.logging.detailed("Checking url {}".format(url))
        result = requests.get(url, auth=( github_account )).json()

        time.sleep(self.SLEEP_TIMEOUT) # Timeout after each request to prevent api overload
        return result

    # Gets number of accessible urls from data response
    def get_num(self, url):
        total_num = 0
        json_data = self.request(url, self.GITHUB_ACCESS_TUPLE)

        if( not ( "total_count" ) in json_data ):
            self.logging.warning("Request failure: {}".format(json_data["message"]))
        else:
            total_num = json_data["total_count"]
            self.logging.info("[{}] projects found for {}".format(total_num, url))

        return total_num

    # Writes received data to output file
    def writedata(self, repo_dicts, i, file):
        
        repo_dicti = repo_dicts[i]
        file.writelines("{} {} {}\n".format(repo_dicti['stargazers_count'], repo_dicti['clone_url'], repo_dicti['forks_count']))

    # Collects data per page
    def collect_paginated_data(self, base_url, total_num, outputFile):
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
                self.logging.debug("{} entries written".format(data_response_length))
            else:
                self.logging.warning("Request failure: {}".format(data["message"]))
                time.sleep(self.SLEEP_TIMEOUT * 3) # Extra timeout, in case too many api events are being called
            self.logging.detailed("-" * self.STRING_REPEAT_CONSTANT)

    # Core class function, requests data from Github and saves valid responses
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
                self.collect_paginated_data(url, total_num, outputFile)
            if ( total_num > self.GITHUB_MAX_INDEX ):
                self.logging.debug("{}+ urls detected. {} skipped".format(self.GITHUB_MAX_INDEX, total_num - self.GITHUB_MAX_INDEX))
            self.logging.info("==" * self.STRING_REPEAT_CONSTANT)

    # Program entry point and opening processes
    def begin(self, language):
        
        self.LANGUAGE = language
        assert not self.LANGUAGE is None, "Language must not be {} -> {}".format(None, self.LANGUAGE)

        self.checkRateLimit()

        output_directory = "output/{}".format(self.LANGUAGE)
        os.makedirs(output_directory, exist_ok = True)

        configuration_settings = []
        configuration_settings.append("Language = {}".format(self.LANGUAGE))
        configuration_settings.append("Range = {} - {}".format(self.calculateIsoDateString(( self.INITIAL_ISO_YEAR, self.INITIAL_ISO_MONTH, self.INITIAL_ISO_DAY )), self.STOP_YEAR))
        configuration_settings.append("Skipped days = {}".format(self.SKIPPED_DAYS))
        configuration_settings.append("Sleep timeout = {}".format(self.SLEEP_TIMEOUT))
        configuration_settings.append("Start = {}".format(datetime.datetime.now()))

        configuration_file = open("{}/{}.configuration".format(output_directory, self.LANGUAGE), "w")
        for parameter in configuration_settings:
            self.logging.info(parameter)
            configuration_file.write("{}\n".format(parameter))
        configuration_file.flush() # Write contents to file

        outputFile = open("{}/{}.output".format(output_directory, self.LANGUAGE), "a")
        outputFile.truncate(0) # Clear any data in file

        self.crawl(outputFile)
        
        configuration_file.write("End = {}".format(datetime.datetime.now()))

        # Close files
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
                newDay = self.maxDays(newMonth)
            else:
                newMonth = 12
                newDay = self.maxDays(newMonth)
                newYear -= 1

        self.logging.detailed("Updated date range {}-{}-{} -> {}-{}-{}".format(month, day, year, newMonth, newDay, newYear))

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

    # Returns string formatted ISO date
    def calculateIsoDateString(self, isoDate):
        year = isoDate[0]
        month = isoDate[1]
        day = isoDate[2]

        monthString = ( "0{}".format(month) )[-2:] # Get last 2 characters of formatted month string
        dayString = ( "0{}".format(day) )[-2:] # Get last 2 characters of formatted day string

        result = "{}-{}-{}".format(year, monthString, dayString) 
        self.logging.debug("ISO DATE for {} is {}".format(isoDate, result))
        return ( result )

    # Checks if user access tuple is authenticated
    def checkRateLimit(self):
        response = self.request("http://api.github.com/rate_limit", self.GITHUB_ACCESS_TUPLE)
        search_limit_per_minute = int(( response["resources"]["search"]["limit"] ))
        isAuthenticated = ( 30 == search_limit_per_minute )


        self.logging.info("Authenticated user and increased api access = {}".format(isAuthenticated))

        self.SLEEP_TIMEOUT = 60 / search_limit_per_minute
        self.logging.detailed("Sleep timeoout set to {}".format(self.SLEEP_TIMEOUT))
