import requests, json
import sys
from tabulate import tabulate

api_key="tao-xxxx"

headers = {
            "accept": "application/json",
            "Authorization": api_key
        }
number_of_valis = 25


#get current block
block_url = "https://api.taostats.io/api/block/v1?limit=1"
block_response = requests.get(block_url, headers=headers)
block_resJson = json.loads(block_response.text)

try:
    block_end = block_resJson['data'][0]['block_number']
except KeyError as e:
    print(f"Error: {e}. Please check the API response and try again.")
    sys.exit(1)

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
total_pages = 1

while page <= total_pages:
    delegation_url = f"https://api.taostats.io/api/delegation/v1?page={page}&limit=200&block_start={block_start}&block_end={block_end}"
    delegation_response = requests.get(delegation_url, headers=headers)
    delegation_resJson = json.loads(delegation_response.text)

    if 'pagination' in delegation_resJson:
        total_pages = delegation_resJson['pagination']['total_pages']
    else:
        total_pages = 1

    if 'data' in delegation_resJson:
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
    else:
        print("No 'data' key found in the API response.")

    page +=1

table_data = []
for index, value in top_valis.items():
    name = value['name']
    stake_now = round(value['stake'],0)
    stake_in = value['delegate']
    stake_out = value['undelegate']
    count = value['count']
    stake_yesterday = round(stake_now +stake_out - stake_in,0)
    stake_change = stake_in - stake_out
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

    table_data.append([name, stake_yesterday, stake_now, count, round(stake_in, digits), -round(stake_out,0), round(stake_change,0)])

print(tabulate(table_data, headers=["Validator", "Stake24", "StakeNow", "Events", "Delegated", "Undelegated", "Stake Change"], tablefmt="grid"))
