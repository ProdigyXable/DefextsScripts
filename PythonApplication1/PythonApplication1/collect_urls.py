
import requests
import time
import os
import getpass
import math

# Github Details
GITHUB_USERNAME = None
ACCESS_TOKEN = "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"

# Github API Settings
GITHUB_MAX_INDEX = 1000
MAX_RESULTS_PER_PAGE = 100
MAX_PAGE_NUMBER = int(GITHUB_MAX_INDEX / MAX_RESULTS_PER_PAGE)

def request(url, github_account):
    return requests.get(url,auth=(github_account)).json()

def get_num(url):
    total_num = 0
    sleep_timeout = 2
    
    json_data=request(url,(GITHUB_USERNAME, ACCESS_TOKEN))
    if(not ("total_count") in json_data):
        print("Reason for request failure: " + json_data["message"])
        time.sleep(sleep_timeout)
    else:
        total_num = json_data["total_count"]
    return total_num

def writedata(repo_dicts, i):
    file = open("output_urls", "a")
    repo_dicti = repo_dicts[i]
     
    file.writelines("{} {} {}".format(repo_dicti['stargazers_count'], repo_dicti['clone_url'], repo_dicti['forks_count']))
    file.writelines("\r\n")

def collect_data(base_url, total_num):
    num = int(total_num / MAX_RESULTS_PER_PAGE) + 1

    for j in range(1, min(num + 1, MAX_PAGE_NUMBER + 2)):
        url = base_url + '&page=' + str(j)
        print("\t - Fetching page: " + str(j))
        data = request(url,(GITHUB_USERNAME, ACCESS_TOKEN))
        
        if("items" in data):

            repo_dicts = data['items']
            
            length = len(repo_dicts)
            
            i = 0
            while(i < length):
                writedata(repo_dicts,i) 
                i += 1
            time.sleep(0)
        else:
            print("Reason for request failure: " + data["message"])
            time.sleep(5)


def main():
    global GITHUB_USERNAME
    global GITHUB_PASSWORD

    GITHUB_USERNAME = input("Input your Github username (needed to increase the number of results):\t")
    #  GITHUB_PASSWORD = getpass.getpass("Input your Github password (needed to increase the number of results):\t")
    LANGUAGE = 'Kotlin'
  
    savedUrls = 0

    ISO_YEAR = 2021
    ISO_MONTH = 5
    ISO_DAY = 21

    NewIsoDate = getIsoDate(ISO_YEAR, ISO_MONTH, ISO_DAY, 1)
    OldIsoDate = NewIsoDate
    
    STOP_YEAR = 2009
    while(NewIsoDate[0] >= STOP_YEAR ):
        SKIPPED_DAYS = 0
        OldIsoDate = getIsoDate(NewIsoDate[0], NewIsoDate[1], NewIsoDate[2], 1)
        NewIsoDate = getIsoDate(OldIsoDate[0], OldIsoDate[1], OldIsoDate[2], SKIPPED_DAYS)

        url = "https://api.github.com/search/repositories?q=language:{}+created:{}..{}&per_page={}".format(LANGUAGE, getIsoString(NewIsoDate), getIsoString(OldIsoDate), MAX_RESULTS_PER_PAGE)
        time.sleep(2)
        
        total_num = get_num(url)

        print("[{}] urls found for request:\t {}".format(total_num, url))
        if (total_num > 0):
            collect_data(url, total_num)
        if (total_num > GITHUB_MAX_INDEX):
            print("{}+ urls detected. {} skipped".format(GITHUB_MAX_INDEX, total_num - GITHUB_MAX_INDEX))

def getIsoDate(year, month, day, decrement):
    newYear = year
    newMonth = month
    newDay = day

    if(newDay > 1):
        newDay = max(newDay - decrement, 1)
    elif(newDay <= 1):
        if(newMonth > 1):
            newMonth -= 1
            newDay = maxDays(newMonth)
        else:
            newMonth = 12
            newDay = maxDays(newMonth)
            newYear -= 1

    return (newYear, newMonth, newDay)

def maxDays(month):
    if(month == 2):
        return 28
    elif(month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12):
        return 31
    else:
        return 30

def getIsoString(isoDate):
    year = isoDate[0]
    month = isoDate[1]
    day = isoDate[2]

    return (str(year) + "-" + ("0" + str(month))[-2:] + "-"  +  ("0" + str(day))[-2:])

for language in ['Kotlin', 'Scala', 'Groovy']:

main()
