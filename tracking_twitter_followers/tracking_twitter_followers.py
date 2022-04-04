# Import libraries
import os
import tweepy as tw
from time import sleep
import pandas as pd
from datetime import datetime as dt
import csv
import numpy as np
import string
import json
import sys
import time
from pathlib import Path
import glob
import sqlite3

# Read in Twitter API keys and token information from stored environment variables
api_key = os.environ.get('TWITTER_API_KEY')
api_secret = os.environ.get('TWITTER_API_SECRET')
access_token_key = os.environ.get('TWITTER_ACCESS_TOKEN_KEY')
access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Pass API keys and tokens to initialize API
auth = tw.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token_key, access_token_secret)
api = tw.API(auth, wait_on_rate_limit = True)

### BEGIN COLLECTION AND CLEANING OF CANDIDATE INFORMATION FROM WEBSCRAPE

"""

In the near-term, this section will be unnecessary and removed from the script. 
It's functions (read_text_file, convert_clean_names_to_string) will be transferred to the webscrape script. 
Output of that file will be housed in a SQL database, and this script will pull in information from that database
using a WHERE clause on STATE_NAME. 

"""

current = os.path.dirname(os.path.realpath("__file__")) # Current file path
parent = os.path.dirname(current) # Parent file path
candidate_folder = "\\sourcing_general_election_candidates\\general_election_candidates_state\\" # Path to list of files

list_of_candidates_path = parent + candidate_folder

# Change directory to read-in .txt files containing a list of candidates in a given state
os.chdir(list_of_candidates_path)

# Initialize an empty list that will hold information on our candidates
candidates_for_analysis = []

def read_text_file(file_path): 

    """
    This function opens each file that ends in .txt, and appends the information to the list above. 

    """

    with open(file_path, 'r') as f: 
        for line in f:
            candidates_for_analysis.append(line.strip())

for file in os.listdir(): 
    if file.endswith(".txt"): 
        file_path = f'{list_of_candidates_path}{file}' # Uses f-string to navigate to the correct folder 
        read_text_file(file_path) # Calls the function to read in .txt files

"""

Candidates for a given state were sourced via web-scrape (BeautifulSoup). The information returned is a list of lists.
As structured, this cannot be fed to the API to find Twitter accounts. 
Instead, convert the list of lists to a string, then replace extraneous / offending characters appropriately.
Finally, remove the last two characters of the string -- they will be ", ".

"""       

candidate_string_result = ' '.join([str(element) for element in candidates_for_analysis])
candidate_string_result = candidate_string_result.replace("['", '')
candidate_string_result = candidate_string_result.replace(" ']", ', ')
candidate_string_result = candidate_string_result[:-2]

def convert_clean_names_to_list(string): 

    """
    This function converts the cleaned names back to a list that can be passed to Twitter. 

    """

    list_of_strings = list(string.split(", "))
    return list_of_strings

candidate_list = convert_clean_names_to_list(candidate_string_result) # Convert the strings back to a list

file_state = file.split("_", 1)[0] # Select the state name from the parent file

### END OF SECTION: COLLECTION AND CLEANING OF CANDIDATE INFORMATION FROM WEBSCRAPE

"""

Since Twitter's API does not currently allow users to see / differentiate accounts based on  the Election Label --
https://help.twitter.com/en/using-twitter/election-labels -- we must query Twitter to return a list accounts
that may be a general election candidate. 

This is an involved process. Given our list of general election candidate names (candidate_string_result), 
we pass those names in for loops to Twitter to return a set of account-specific information that we use to 
manually process, differentiate, and discern account IDs for general election candidates -- e.g., the primary target. 

Specifically, we request screen names, ids, locations, url, and descriptions for each probable account returned by Twitter. 
Next, these are zipped into a list wherein the information is grouped by position. 
That is, all info in index position 5 in all lists are grouped together. 

Now, manually review each row for information to determine which account is a general election candidate. 
This process will differ from state to state, with drops determined by specific place in index of true candidates.

Until such time Twitter includes the ability to query this information via the API, manual processing is requried. 
That said, this is an open question: 
https://twittercommunity.com/t/share-your-input-on-adding-tweet-profile-labels-to-the-twitter-api-v2/167678.

"""

### BEGIN COLLECTION OF POTENTIAL CANDIDATES' TWITTER ACCOUNTS  

# Initialize empty lists to hold account information about possible candidate Twitter accounts
potential_candidate_accounts = []
potential_candidate_account_ids = []
potential_candidate_account_location = []
potential_candidate_account_url = []
potential_candidate_account_description = []

counter = 0

# While there are still potentials candidates in the candidate_list
while counter < len(candidate_list): 
    for user in candidate_list: 
        accounts = api.search_users(user) # Call the API to search for users with similar names
        for account in accounts: 
            potential_candidate_accounts.append(account.screen_name) # Append screen name to the relevant list
            potential_candidate_account_ids.append(account.id_str) # Append ID to the relevant list
            potential_candidate_account_location.append(account.location) # Append location to the relevant list
            potential_candidate_account_url.append(account.url) # Append url in profile to the relevant list
            potential_candidate_account_description.append(account.description) # Append description to the relevant list
            
            counter += 1 # Increment through list until exhausted
            
# Instantiate a list that is the same length as the list we passed to Twitter with the state name as the only value
potential_candidate_accounts_state_analysis = [file_state] * len(potential_candidate_accounts)

# Zip the lists into another list, so each place in index aligns to the same potential candidate
zipped_candidate_list = list(zip(potential_candidate_accounts, 
                        potential_candidate_account_ids, 
                        potential_candidate_account_location, 
                        potential_candidate_account_url, 
                        potential_candidate_account_description,
                        potential_candidate_accounts_state_analysis))

# Convert zipped list to dataframe, initialize column names as appropriate
candidate_twitter_info = pd.DataFrame(data = zipped_candidate_list, columns = ['SCREEN_NAME', 'ACCOUNT_ID', 'LOCATION', 'URL', 'DESCRIPTION', 'STATE'])
candidate_twitter_info = pd.DataFrame(candidate_twitter_info)

### END OF SECTION: COLLECTION OF POTENTIAL CANDIDATES' TWITTER ACCOUNTS

"""

This section depends on the structure of the collated data. It will need to be amended across excutions.
The below is an example of cleaning data for Texas. 

"""
### BEGIN MANUAL PROCESSING SECTION

# Drop non-target accounts from the dataframe based on index position
candidate_twitter_info.drop(candidate_twitter_info.index[1:15], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[3:23], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[4:22], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[5:12], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[5], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[7:25], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[8:47], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[10:28], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[12:17], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[16], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[18:36], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[19:31], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[20:39], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[23:43], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[24:41], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[25], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[21:23], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[24:60], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[25], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[26:44], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[27:45], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[29:32], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[31:49], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[32:51], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[34:52], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[35:54], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[37:55], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[38:77], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[39:58], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[40:59], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[42:60], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[43:45], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[45:62], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[46:54], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[48:53], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[50:68], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[54:72], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[55:74], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[57:76], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[58:99], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[59:62], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[61:79], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[62:81], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[64:69], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[65:88], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[66:87], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[67:84], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[69:87], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[70:89], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[72:110], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[74:134], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[76:93], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[78:96], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[80:89], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[81:86], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[82:98], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[84:104], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[86:104], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[87:126], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[89:107], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[90:95], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[92:94], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[93:113], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info.drop(candidate_twitter_info.index[94:114], axis = 0, inplace = True)
candidate_twitter_info.reset_index(level = 0, inplace = True, drop = True)

"""

The search to surface potential general election candidates wasn't 100 % accurate. 
So given the list of candidates obtained from the Wikimedia API, we manually searched to see if a given 
candidate in fact had a Twitter account. For those that do have accounts, 
instantiate a list of their handles to pass to Twitter once again and repeat the process above. 

As of the date of execution, 10 candidates for Congress in Texas did not have Twitter accounts, including: 
Jimmy leon, Jamie Kaye Jordan, Robert Schafranek, Julio Garza, James Harris, Patrick Gillespie, 
Dan McQueen, Michael Rodriguez, Rod Lingsch, and Duncan Klussman. 

"""

manual_candidate_list = ['sandeepfortexas', 
                         'rubentx15', 
                         'RVillarrealTX21', 
                         'derrikgay', 
                         'JCisnerosTX', 
                         'texas_sandra', 
                         'CasandraLGarcia', 
                         'JasmineForUS', 
                         'JaneHopeTX',
                         'GregCasar', 
                         'DianaforTexas'
                        ]

# Initialize empty lists to hold account information about possible candidate Twitter accounts
manual_potential_candidate_accounts = []
manual_potential_candidate_account_ids = []
manual_potential_candidate_account_location = []
manual_potential_candidate_account_url = []
manual_potential_candidate_account_description = []

counter = 0

# While there are still potentials candidates in the candidate_list
while counter < len(manual_candidate_list): 
    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts: 
            manual_potential_candidate_accounts.append(account.screen_name) # Append screen name to the relevant list
            manual_potential_candidate_account_ids.append(account.id_str) # Append id to the relevant list
            manual_potential_candidate_account_location.append(account.location) # Append location in profile to the relevant list
            manual_potential_candidate_account_url.append(account.url) # Append url in profile to the relevant list
            manual_potential_candidate_account_description.append(account.description) # Append description in profile to the relevant list
            
            counter += 1 # Increment through list until exhausted

# Instantiate a list that is the same length as the list we passed to Twitter with the state name as the only value
manual_potential_candidate_accounts_state_analysis = [file_state] * len(manual_potential_candidate_accounts)

# Zip the lists into another list, so each place in index aligns to the same potential candidate
manual_zipped_manual_candidate_list = list(zip(manual_potential_candidate_accounts, 
                        manual_potential_candidate_account_ids, 
                        manual_potential_candidate_account_location, 
                        manual_potential_candidate_account_url, 
                        manual_potential_candidate_account_description,
                        manual_potential_candidate_accounts_state_analysis))

# Convert zipped list to dataframe, initialize column names as appropriate
manual_candidate_twitter_info = pd.DataFrame(data = manual_zipped_manual_candidate_list, columns = ['SCREEN_NAME', 'ACCOUNT_ID', 'LOCATION', 'URL', 'DESCRIPTION', 'STATE'])
candidate_twitter_info_manual = pd.DataFrame(manual_candidate_twitter_info)

# Drop non-target accounts from the dataframe based on index position
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[4], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[5:11], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[6:25], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[7], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[11:14], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)
candidate_twitter_info_manual.drop(candidate_twitter_info_manual.index[8], axis = 0, inplace = True)
candidate_twitter_info_manual.reset_index(level = 0, inplace = True, drop = True)

# Concat the two dataframes vertically, and then convert to a list that contains only their ACCOUNT_IDs 
# We pass this inforamtion to twitter in the get_followers_id function to source, append, and archive followers
candidate_twitter_info = pd.concat([candidate_twitter_info, candidate_twitter_info_manual], axis=0, ignore_index=True)
general_election_candidates_twitter_ids_list = candidate_twitter_info.ACCOUNT_ID.values.tolist()

### END OF SECTION: MANUAL PROCESSING SECTION

### BEGIN TRANSFER OF CANDIDATE TWITTER ACCOUNT DATA TO SQL DATABASE FOR STORAGE

# Initialize SQL connection
sql_connect = sqlite3.connect(r"C:\sqlite\federal_election_bot_analysis\candidate_twitter_accounts.db")
cursor = sql_connect.cursor()

print('Length of database before transfer.') # Check on the current length of the database 
cursor.execute('''SELECT * CANDIDATE_TWITTER_INFO''')
print(len(cursor.fetchall()))
sql_connect.commit()

# Push the dataframe to the appropriate SQl database
candidate_twitter_info.to_sql(name = 'CANDIDATE_TWITTER_INFO', # Name of the table in db
                                  con = sql_connect, 
                                  if_exists = 'append', # Append the new rows of data
                                  index = False)

sql_connect.commit() # Commit the change

print('Length of database after transfer.') # Check to ensure the database did in fact update by comparing the length of db
cursor.execute('''SELECT * FROM CANDIDATE_TWITTER_INFO''')
print(len(cursor.fetchall()))
sql_connect.commit()
cursor.close()
sql_connect.close()

### END TRANSFER OF DATA TO SQL DATABASE

"""

This section loops over a list of general election candidates' Twitter accounts, 
queries the Twitter API to return a list of follower_ids for each account, 
and concatenates the results into a dataframe tha we pass to the SQL database. 

"""

## BEGIN COLLECTION OF CANDIDATE FOLLOWERS' IDS

global candidate_id_followers_ids
candidate_id_followers_ids = pd.DataFrame(columns = ['FOLLOWER_ID', 'CANDIDATE_ID'])
global df_helper

def get_candiate_follower_ids(general_election_candidates_twitter_ids_list):
    for candidate in general_election_candidates_twitter_ids_list:
        follower_ids = []
        candidate_id = []

        for ids_tweepy in tw.Cursor(api.get_follower_ids, user_id = candidate).pages(): 
            follower_ids.extend(ids_tweepy)

        for candidate in general_election_candidates_twitter_ids_list: 
            candidate_id = [candidate] * len(follower_ids)
            
            for candidate in general_election_candidates_twitter_ids_list: 
                candidate_id_followers_zipped =  list(zip(follower_ids, candidate_id))
                global df_helper
                df_helper = candidate_id_followers_ids.append(pd.DataFrame(candidate_id_followers_zipped, 
                                                                           columns = candidate_id_followers_ids.columns))

get_candiate_follower_ids(general_election_candidates_twitter_ids_list) # Call the function to get follower_ids
candidate_id_followers_ids = candidate_id_followers_ids.append(df_helper) # Append new follower_ids to the df

### END OF SECTION: COLLECTION OF CANDIDATE FOLLOWERS' IDS

### BEGIN TRANSFER OF DATA TO SQL DATABASE FOR STORAGE AND FUTURE ANALYSIS

# Initialize SQL connection
sql_connect = sqlite3.connect(r"C:\sqlite\federal_election_bot_analysis\candidate_twitter_accounts.db")
cursor = sql_connect.cursor()

print('Length of database before transfer.') # Check on the current length of the database 
cursor.execute('''SELECT * FROM CANDIDATE_ID_FOLLOWER_ID''')
print(len(cursor.fetchall()))
sql_connect.commit()

# Push the dataframe to the appropriate SQl database
candidate_id_followers_ids.to_sql(name = 'CANDIDATE_ID_FOLLOWER_ID', # Name of the table in db
                                  con = sql_connect, 
                                  if_exists = 'append', # Append the new rows of data
                                  index = False)

sql_connect.commit() # Commit the change

print('Length of database after transfer.') # Check to ensure the database did in fact update by comparing the length of db
cursor.execute('''SELECT * FROM CANDIDATE_ID_FOLLOWER_ID''')
print(len(cursor.fetchall()))
sql_connect.commit()
cursor.close()
sql_connect.close()

### END OF SECTION: TRANSFER OF DATA TO SQL DATABASE

##### END OF SCRIPT AS OF 03 APRIL 2022 ##### 

