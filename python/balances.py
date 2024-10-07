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


api_key="<put you API key here>"
coldkey = "5HBtpwxuGNL1gwzwomwR7sjwUt8WXYSuWcLYN6f9KpTZkP4k"
start_date = "2024-01-01T00:00:00Z"
end_date = "2025-01-01T00:00:00Z"

#Get the daily account balances
total_address_history = []
count = 200
page =1

while count >0:
    url = f"https://api.taostats.io/api/v1/address/history?address={coldkey}&timestamp_start={start_date}&timestamp_end={end_date}&limit={count}&page={page}&order=timestamp:asc"
    
    headers = {
        "accept": "application/json",
        "Authorization": api_key
    }
    
    response = requests.get(url, headers=headers)
    resJson = json.loads(response.text)
    new_count = resJson['count']
    total_address_history+=resJson['address_history']
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