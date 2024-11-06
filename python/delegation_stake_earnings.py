import requests, json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import decimal
from datetime import datetime, timedelta
from rich import print


#this grows on balances.py, in that it includes all delegation and undelegation events from your staked balance.
#This is more accurate a a result.
#where does this fail? If you are a miner, and you had a neuron get de-registered - that stake is automatically transferred to your coldkey
#we dont get that here.  Just stake earnings and delegation and undelegation events

#initially I was going to print the results DoD - but with delegation timings - this became more complcated than we really need. (See comment at end)

#to run this, you'll need an API key (https://dash.taostats.io)
#the coldkey is the wallet you wish to examine - default is the OTF foundation wallet
#start & end dates

api_key="<your apikey>"

coldkey = "5HBtpwxuGNL1gwzwomwR7sjwUt8WXYSuWcLYN6f9KpTZkP4k"
#unix timestamps
start_date = 1704085200
end_date = 1735707600
# if this is a new wallet - thr first delegation event must be ignored.
## if this is an existing wallet - the first delegtion event must be recorded
include_first_delegation = False

#sometimes the chain spits out a time with milliseconds.. Sometimess it doesnt.  Its annoying.
#this fixes it.
def stupid_time_fix(timestamp):
    if len(timestamp) > 20:
        date_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        date_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    return formatted_date
		
		
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
				
				
				
				
#extract the day over day staked sum - 
#get the DOD change and then add them all up

dod_staked = {}
dod_staked_sum =0
#print(f"date, Free, staked, total, Free DOD, staked DOD, total DOD")
for index, date in enumerate(total_address_history):
    timestamp = date['timestamp']
    day = stupid_time_fix(timestamp)
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
    #print(f"{day}, {free}, {staked}, {total}, {free_difference}, {staked_difference}, {total_difference}")
    dod_staked[day] = staked_difference
    dod_staked_sum +=staked_difference
		
		
##get all delegation transfers for the coldkey
all_delegation_events = []

count = 200
page =1

while count >0:
    url = f"https://api.taostats.io/api/delegation/v1?nominator={coldkey}&timestamp_start={start_date}&timestamp_end={end_date}&limit={count}&page={page}&order=block_number_asc"
    
    headers = {
        "accept": "application/json",
        "Authorization": api_key
    }
    
    response = requests.get(url, headers=headers)
    resJson = json.loads(response.text)
    new_count = resJson['pagination']['total_items']
    all_delegation_events+=resJson['data']
    if new_count < 200 and new_count == count:
        #We did the last query
        break
    else:
        #we should keep going
        count = new_count
        page +=1
	
	
#now we find all the delegtion events and sum them (or subtract if undelegation

summed_delegation_events = {}
sum_delegation_events =0

# if this is a new wallet - we want to ignore the first delegation 
include_delegation = True
if not include_first_delegation:
    #if ythis is false - we want to skip the first delegation
    include_delegation = False


for event in all_delegation_events:
    action = event['action']
    day = stupid_time_fix(event['timestamp'])
    amount = float(event['amount'])/1e9

    ##add the resullst if it is delegation
    if action == "DELEGATE":
        if include_delegation:
            sum_delegation_events +=amount
            if day in summed_delegation_events:
                summed_delegation_events[day] += amount
            else:
                summed_delegation_events[day] = amount
        else:
            #we skipped the first delegtion event, dont skip any more
            include_delegation = True
    
    else:
    #un delegatte
        sum_delegation_events -=amount
        if day in summed_delegation_events:
            summed_delegation_events[day] += -amount
        else:
            summed_delegation_events[day] = -amount
    
    #print(day, action, amount)
#print(summed_delegation_events)

#so doing this day over day ensd up being a PITA - sometimes the delegation was before the balance check.. sometimes after.
# and really - we dont care about stake day over day (you can  remove the comments on the print statements if you do)
#what we want to know is how much stake was earned over the period of days
# we know the DOD earnings, and the delegtion and undelegtion evenst.
# we have them all summed
#so dont do the extra work for day to day.
print("total tao delegated undelegated" , sum_delegation_events," total change in stake: ", dod_staked_sum)
total_stake_earnings = dod_staked_sum-sum_delegation_events
print("total stake earnings: ", total_stake_earnings)
	