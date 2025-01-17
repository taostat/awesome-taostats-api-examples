'''
This script grabs the top 25 validators by stake. 

It then collects all the delegation events for the last 24 hours (7200 blocks) and adds up all the delegation events for the top 25 delegators

It prints out for each validator:
stake yesterday
stake now
count - number of delegation events
delegation in - staked to the vali
delegation out - unstaked from the vali

'''

import requests, json

api_key=""


headers = {
            "accept": "application/json",
            "Authorization": api_key
        }
number_of_valis = 25


#get current block
block_url = "https://api.taostats.io/api/block/v1?limit=1"
block_response = requests.get(block_url, headers=headers)
block_resJson = json.loads(block_response.text)
block_end = block_resJson['data'][0]['block_number']

#start is 7200 blocks ago
block_start = block_end -7200
#print(block_start, block_end)


# get top 25 valis name & stake

vali_url = f"https://api.taostats.io/api/validator/latest/v1?limit={number_of_valis}&order=stake_desc"
vali_response = requests.get(vali_url, headers=headers)
vali_resJson = json.loads(vali_response.text)

top_valis ={}
vali_data = vali_resJson['data']
for vali in vali_data:
    hotkey = vali['hotkey']['ss58']
    name = vali['name'] or hotkey[:5]

    stake = float(vali['stake'])/1e9
    top_valis[hotkey]= {"name":name, "stake":stake, "count":0,"delegate":0, "undelegate":0}

#get all delegation evenst for the last 24 hours and add to the validator data

page =1
total_pages=2
while page< total_pages:
    delegation_url = f"https://api.taostats.io/api/delegation/v1?page={page}&limit=200&block_start={block_start}&block_end={block_end}"
    delegation_response = requests.get(delegation_url, headers=headers)
    delegation_resJson = json.loads(delegation_response.text)
    total_pages = delegation_resJson['pagination']['total_pages']
    page +=1
    #now get all the delegation events
    for delegation in delegation_resJson['data']:
        hotkey = delegation['delegate']['ss58']
        amount = float(delegation['amount'])/1e9
        if hotkey in top_valis:
            top_valis[hotkey]['count'] +=1
            #add the data to the array
            if delegation['action'] == "UNDELEGATE":
                top_valis[hotkey]['undelegate'] += amount
            else:
                top_valis[hotkey]['delegate'] += amount


                                       
print("validator\t\t\t Stake24 \t stakeNow \t Events  delegated \t undelegated")

for index, value in top_valis.items():
    name = value['name']
    length = 25
    if len(name) < length:
        name += ' ' * (length - len(name))
    stake_now = round(value['stake'],0)
    stake_in = value['delegate']
    stake_out = value['undelegate']
    count = value['count']
    stake_yesterday = round(stake_now +stake_out - stake_in,0)
    #silly display stuff
    digits =0
    if stake_in < 1:
        digits = 5
    elif stake_in < 10:
        digits = 4
    elif stake_in < 100:
        digits = 3
    elif stake_in < 1000:
        digits = 2
    elif stake_in < 10000:
        digits =1

    print(name, '\t', stake_yesterday, '\t', stake_now, '\t', count, '\t', round(stake_in,digits), '\t', round(-stake_out,0))