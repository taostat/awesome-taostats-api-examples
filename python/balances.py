import requests, json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import decimal
from datetime import datetime, timedelta
from rich import print


#to run this, you'll need an API key (https://dash.taostats.io)
#the coldkey is the wallet you wish to examine - default is the OTF foundation wallet
#start & end dates



api_key="<tao-3c7faaee-3e61-417e-a5f1-e706eef3fa4e:f4052912>"

coldkey = "5FWVerQFjFPcpFDHxwpXvq4yMoAQGfqaBTEkRmi6gPxqsMcT"

#unix timestamps
start_date = 1735689600
end_date = 1751416324

#Get the daily account balances
total_address_history = []
count = 200
page =1

while count >0:
    url = f"https://api.taostats.io/api/account/history/v1?address={coldkey}&timestamp_start={start_date}&timestamp_end={end_date}&limit={count}&page={page}&order=timestamp_asc"
    
    headers = {
        "accept": "application/json",
        "Authorization": api_key
    }
    
    response = requests.get(url, headers=headers)
    resJson = json.loads(response.text)
    new_count = resJson['pagination']['total_items']
    total_address_history+=resJson['data']
    if new_count < 200 and new_count == count:
        #We did the last query
        break
    else:
        #we should keep going
        count = new_count
        page +=1
				
#create a CSV			
print(f"date, Free, staked, total, Free DOD, staked DOD, total DOD")

for index, date in enumerate(total_address_history):
    total = float(date['balance_total'])/1e9
    staked = float(date['balance_staked'])/1e9
    free = float(date['balance_free'])/1e9
    total_difference = 0
    staked_difference = 0
    free_difference = 0
    if index >0:
        total_difference = total - float(total_address_history[index-1]['balance_total'])/1e9
        staked_difference = staked - float(total_address_history[index-1]['balance_staked'])/1e9
        free_difference = free - float(total_address_history[index-1]['balance_free'])/1e9
    print(f"{date['timestamp']}, {free}, {staked}, {total}, {free_difference}, {staked_difference}, {total_difference}")
