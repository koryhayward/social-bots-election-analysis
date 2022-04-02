#!/usr/bin/env python
# coding: utf-8

# In[5]:


!pip3 install tweepy

# Import libraries
import os
import tweepy as tw
import pandas as pd
from datetime import datetime as dt
import csv
import numpy as np
import string
from datetime import timedelta
import bamboolib as bam
import json
import sys
import time
from pathlib import Path
import glob

run_stamp = dt.now().strftime("%Y-%m-%d")


# In[ ]:


from twilio.rest import Client
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
client.messages.create(from_ = os.environ.get('TWILIO_PHONE_NUMBER'),
to = os.environ.get('KH_PHONE_NUMBER'),
body = 'Your script has started running!')


# In[ ]:


# Read in Twitter API keys and token information from stored environment variables
api_key = os.environ.get('TWITTER_API_KEY')
api_secret = os.environ.get('TWITTER_API_SECRET')
access_token_key = os.environ.get('TWITTER_ACCESS_TOKEN_KEY')
access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Pass API keys and tokens to initialize API
auth = tw.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token_key, access_token_secret)
api = tw.API(auth, wait_on_rate_limit = True)


# In[6]:


current = os.path.dirname(os.path.realpath("__file__"))
parent = os.path.dirname(current)
candidate_folder = "\\sourcing_general_election_candidates\\general_election_candidates_state\\"
list_of_candidates_path = parent + candidate_folder


# In[ ]:


os.chdir(list_of_candidates_path)

candidates_for_analysis = []

def get_followers_ids(user_id): 
    ids = []
    page_count = 0 
    
    for page in tw.Cursor(api.get_follower_ids, id = user_id, count = 5000).pages():
        page_count += 1
        print("Getting page {} for {}'s followers' IDs".format(page_count, user_id))
        ids.extend(page)
        
        path_to_output = current + "\\" + file_state + "\\id_output\\"
        
        os.makedirs(path_to_output)
        
        path = current + "\\" + file_state + "\\id_output\\"+ "{}_followers_{}.csv".format(user_id, run_stamp)
        to_write_file = path
        with open(to_write_file, mode = 'a') as csv_file:
            writer = csv.writer(csv_file, delimiter = ',')
            writer.writerow(map(lambda x: [x], str(ids)))
            csv_file.closed
            
            return ids

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

Candidates for a given state were sourced using the Wikimedia API. The information returned is a list of lists.
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

file_state = file.split("_", 1)[0]

potential_candidate_accounts = []
potential_candidate_account_ids = []
potential_candidate_account_location = []
potential_candidate_account_url = []
potential_candidate_account_description = []

counter = 0

while counter < len(candidate_list): 
    for user in candidate_list: 
        accounts = api.search_users(user)
        for account in accounts: 
            potential_candidate_accounts.append(account.screen_name)

    for user in candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            potential_candidate_account_ids.append(account.id_str)

    for user in candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            potential_candidate_account_location.append(account.location)

    for user in candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            potential_candidate_account_url.append(account.url)

    for user in candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            potential_candidate_account_description.append(account.description)

            counter += 1
    potential_candidate_accounts_state_analysis = [file_state] * len(potential_candidate_accounts)

zipped_candidate_list = list(zip(potential_candidate_accounts, 
                        potential_candidate_account_ids, 
                        potential_candidate_account_location, 
                        potential_candidate_account_url, 
                        potential_candidate_account_description,
                        potential_candidate_accounts_state_analysis))

candidate_twitter_info = pd.DataFrame(data = zipped_candidate_list, columns = ['SCREEN_NAME', 'ACCOUNT_ID', 'LOCATION', 'URL', 'DESCRIPTION', 'STATE'])
candidate_twitter_info = pd.DataFrame(candidate_twitter_info)
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

manual_potential_candidate_accounts = []
manual_potential_candidate_account_ids = []
manual_potential_candidate_account_location = []
manual_potential_candidate_account_url = []
manual_potential_candidate_account_description = []

counter = 0

while counter < len(manual_candidate_list): 
    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts: 
            manual_potential_candidate_accounts.append(account.screen_name)

    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            manual_potential_candidate_account_ids.append(account.id_str)

    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            manual_potential_candidate_account_location.append(account.location)

    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            manual_potential_candidate_account_url.append(account.url)

    for user in manual_candidate_list: 
        accounts = api.search_users(user)
        for account in accounts:         
            manual_potential_candidate_account_description.append(account.description)

            counter += 1

manual_potential_candidate_accounts_state_analysis = [file_state] * len(manual_potential_candidate_accounts)

manual_zipped_manual_candidate_list = list(zip(manual_potential_candidate_accounts, 
                        manual_potential_candidate_account_ids, 
                        manual_potential_candidate_account_location, 
                        manual_potential_candidate_account_url, 
                        manual_potential_candidate_account_description,
                        manual_potential_candidate_accounts_state_analysis))

manual_candidate_twitter_info = pd.DataFrame(data = manual_zipped_manual_candidate_list, columns = ['SCREEN_NAME', 'ACCOUNT_ID', 'LOCATION', 'URL', 'DESCRIPTION', 'STATE'])
candidate_twitter_info_manual = pd.DataFrame(manual_candidate_twitter_info)
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

candidate_twitter_info = pd.concat([candidate_twitter_info, candidate_twitter_info_manual], axis=0, ignore_index=True)
general_election_candidates_twitter_ids_list = candidate_twitter_info.ACCOUNT_ID.values.tolist()
    
if __name__ == "__main__": 
    for user_id in general_election_candidates_twitter_ids_list: 
        get_followers_ids(user_id)


# In[ ]:


ipynb_file_name = os.path.dirname(os.path.realpath('__file__')).rsplit('\\',1)[1]
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
client.messages.create(from_ = os.environ.get('TWILIO_PHONE_NUMBER'),
to = os.environ.get('KH_PHONE_NUMBER'),
body = 'Your script has finished running! Head back over to your machine to see the output.')