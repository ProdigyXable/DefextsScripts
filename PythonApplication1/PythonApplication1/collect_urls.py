
import requests
import time
import os
import getpass
import math
import log

class UrlCollector (object):

    """Crawls Github for a given progrmaming languages and retrieves all public repositories created between two date ranges"""
    # LOG
    outputStream = None

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
    ISO_YEAR = 2021
    ISO_MONTH = 5
    ISO_DAY = 21

    # END POINT CONFIGURATION
    STOP_YEAR = 2009

    # TIMEOUT
    SLEEP_TIMEOUT = 3

    def __init__(self, logLevel, github_username, access_token):
        assert self.SKIPPED_DAYS >= self.MINIMUM_SKIPPED_DAYS, "Number of skipped days must be at least 0" 
        
        self.GITHUB_USERNAME = github_username
        assert not self.GITHUB_USERNAME is None, "Username must not be {}".format(None)
        
        self.ACCESS_TOKEN = access_token
        assert not self.ACCESS_TOKEN is None, "Access token must not be {}".format(None)

        self.GITHUB_ACCESS_TUPLE = ( self.GITHUB_USERNAME, self.ACCESS_TOKEN )
        self.outputStream = log.Log(logLevel)

    def request(self, url, github_account):
        return requests.get(url, auth=( github_account )).json()

    def get_num(self, url):
        total_num = 0
    
        json_data = self.request(url, self.GITHUB_ACCESS_TUPLE)
        self.outputStream.debug("Checking url {}".format(url))

        if( not ( "total_count" ) in json_data ):
            self.outputStream.warning("Reason for request failure = {}".format(json_data["message"]))
            time.sleep(self.SLEEP_TIMEOUT)
        else:
            total_num = json_data["total_count"]
            self.outputStream.info("[{}] founds for {}".format(total_num, url))

        return total_num

    def writedata(self, repo_dicts, i):
        file = open("output_{}".format(self.LANGUAGE), "a")
        repo_dicti = repo_dicts[i]
     
        file.writelines("{} {} {}".format(repo_dicti['stargazers_count'], repo_dicti['clone_url'], repo_dicti['forks_count']))
        file.writelines("\r\n")

        self.outputStream.debug("Contents of {} written to".format(file.name))

    def collect_data(self, base_url, total_num):
        num = int(total_num / self.MAX_RESULTS_PER_PAGE) + 1

        for pageNum_index in range(1, min(num + 1, self.MAX_PAGE_NUMBER + 2)):
            url = "{}&page={}".format(base_url, str(pageNum_index))
            self.outputStream.info("\t - Fetching page: {}".format(pageNum_index))
            data = self.request(url, self.GITHUB_ACCESS_TUPLE)
        
            if( "items" in data ):
                dictionaryIteration_index = 0
                repo_dicts = data['items']
                length = len(repo_dicts)
                            
                while( dictionaryIteration_index < length ):
                    self.writedata(repo_dicts,dictionaryIteration_index) 
                    dictionaryIteration_index += 1
                time.sleep(self.SLEEP_TIMEOUT)
            else:
                self.outputStream.debug("Reason for request failure: {}".format(data["message"]))
                time.sleep(self.SLEEP_TIMEOUT * 3)


    def crawl(self, language):
        self.LANGUAGE = language
        assert not self.LANGUAGE is None, "Language must not be {} -> {}".format(None, self.LANGUAGE)
        
        self.outputStream.print("Processing urls for {}".format(self.LANGUAGE))
        self.outputStream.print("-------------------")
               
        NewIsoDate = self.getIsoDate(self.ISO_YEAR, self.ISO_MONTH, self.ISO_DAY, 1)
        OldIsoDate = NewIsoDate

        self.outputStream.detailed("Constructing initial date range starting from {}".format(OldIsoDate))
        
        while( NewIsoDate[0] >= self.STOP_YEAR ):
            
            OldIsoDate = self.getIsoDate(NewIsoDate[0], NewIsoDate[1], NewIsoDate[2], 1)
            NewIsoDate = self.decrementDate(OldIsoDate)

            url = "https://api.github.com/search/repositories?q=language:{}+created:{}..{}&per_page={}" \
                .format(self.LANGUAGE, \
                self.getIsoString(NewIsoDate), \
                self.getIsoString(OldIsoDate), \
                self.MAX_RESULTS_PER_PAGE)

            time.sleep(self.SLEEP_TIMEOUT)
        
            total_num = self.get_num(url)

            if ( total_num > 0 ):
                self.collect_data(url, total_num)
            if ( total_num > self.GITHUB_MAX_INDEX ):
                self.outputStream.debug("{}+ urls detected. {} skipped".format(self.GITHUB_MAX_INDEX, total_num - self.GITHUB_MAX_INDEX))

    def getIsoDate(self, year, month, day, decrement):
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

        self.outputStream.debug("\t - {}-{}-{} -> {}-{}-{}".format(day, month, year, newDay, newMonth, newYear))
        return ( newYear, newMonth, newDay )

    def decrementDate(self, OldIsoDate):
        result = None

        if( self.SKIPPED_DAYS > 0 ):
            result = self.getIsoDate(OldIsoDate[0], OldIsoDate[1], OldIsoDate[2], self.SKIPPED_DAYS)
            self.outputStream.detailed("Decrementing date from {} to {}".format(OldIsoDate, result))
        else:
            result = OldIsoDate      
            self.outputStream.detailed("Setting date range to {} - {}".format(OldIsoDate, result))

        return result

    def maxDays(self, month):
        result = None
        if( month == 2 ):
            result = 28
        elif( month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12 ):
            result = 31
        else:
            result = 30

        self.outputStream.debug("Max days for month {} is {}".format(month, result))
        return result

    def getIsoString(self, isoDate):
        year = isoDate[0]
        month = isoDate[1]
        day = isoDate[2]

        monthString = ( "0{}".format(month) )[-2:]
        dayString = ( "0{}".format(day) )[-2:]

        result = "{}-{}-{}".format(year, monthString, dayString) 
        self.outputStream.debug("ISO DATE for {} is {}".format(isoDate, result))
        return ( result )

# -- START --- #
github_username = input("Input your Github username (needed to increase the number of results):\t")
access_token = getpass.getpass("Input access token: \t")

for language in [ 'Kotlin', 'Scala', 'Groovy' ]:
    uc = UrlCollector(log.Log.DETAILED, github_username, access_token)
    uc.crawl(language)