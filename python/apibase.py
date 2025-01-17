# api base
"""
Use this program as a template for calling the Taostats API
It collects the data into a pandas dataframe and then saves it to a csv file
"""

import requests
import json
import pandas as pd
import sys
import os
import pathlib
import time


class APIClient:
    """
    A class to handle sending API requests.

    Attributes:
    ----------
    base_url (str): The base URL of the API.
    api_key (str, optional): The API key to use for authentication. Defaults to None.
    headers (dict, optional): The default headers to use for requests. Defaults to None.
    max_retries (int, optional): The maximum number of retries if the API returns a 429 (too many requests) status code. Defaults to 3.
    retry_delay (int, optional): The delay in seconds between retries. Defaults to 60.

    Methods:
    -------
    get_json(endpoint, params=None, headers=None, max_retries=None, retry_delay=None):
        Makes an API call to the specified endpoint with optional parameters.

    Raises:
    ------
    requests.RequestException: If there was an error sending the request.
    ValueError: If the response was not valid JSON.
    RuntimeError: If the maximum number of retries was exceeded.
    """

    def __init__(self, base_url, api_key=None, headers=None, max_retries=3, retry_delay=60):
        """
        Initializes the APIClient with the base URL and optional API key, headers, max retries, and retry delay.

        Parameters:
        ----------
        base_url (str): The base URL of the API.
        api_key (str, optional): The API key to use for authentication. Defaults to None.
        headers (dict, optional): The default headers to use for requests. Defaults to None.
        max_retries (int, optional): The maximum number of retries if the API returns a 429 status code. Defaults to 3.
        retry_delay (int, optional): The delay in seconds between retries. Defaults to 60.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers

    def get_json(self, endpoint, params=None, headers=None, max_retries=None, retry_delay=None):
        """
        Makes an API call to the specified endpoint with optional parameters.

        Parameters:
        ----------
        endpoint (str): The endpoint to call.
        params (dict, optional): The query parameters to pass. Defaults to None.
        headers (dict, optional): The headers to pass. Defaults to None.
        max_retries (int, optional): The maximum number of retries if the API returns a 429 status code. Defaults to the instance's max_retries.
        retry_delay (int, optional): The delay in seconds between retries. Defaults to the instance's retry_delay.

        Returns:
        -------
        dict: The API response.
        """
        call_max_retries = self.max_retries if max_retries is None else max_retries
        call_retry_delay = self.retry_delay if retry_delay is None else retry_delay

        if self.api_key is not None:
            self.headers['Authorization'] = f'{self.api_key}'
            
        if headers:
            self.headers.update(headers)

        url = f'{self.base_url}{endpoint}'
        retries = 0
        while retries <= call_max_retries: 
            try:
                response = requests.get(url, params=params, headers=self.headers)
                if response.status_code == 429:
                    # API rate limit exceeded, retry after delay
                    retry_after = int(response.headers['Retry-After']) if 'Retry-After' in response.headers else call_retry_delay
                    print(f'Rate limit exceeded, retrying in {retry_after} seconds...')
                    time.sleep(retry_after)
                    retries += 1
                elif response.status_code == 200:
                    return response.json()
                else:
                    print(f'{response.status_code} - {response.text}')
                    return None
            except requests.exceptions as e:
                print('Error:', e)
                return None
        if retries > call_max_retries:
                print('To many retries returning None')
        return None




# Setup the API client with the taostats URL, base headers and API key
API_url = 'https://api.taostats.io'

api_key = os.environ.get('API_KEY') 
# Alternitive to using a env variable
# api_key = 'the quick brown fox'

headers = {
    "accept": 'application/json',
}
taostats_API = APIClient(base_url=API_url,api_key=api_key,headers=headers,retry_delay=21)


# Get Subnet count
endpoint  = "/api/stats/latest/v1"
stats_json = taostats_API.get_json(endpoint=endpoint)
if stats_json is not None:
    subnetcount = stats_json['data'][0]['subnets']


#  prepare the arguments for the "get_json" call
endpoint  = "/api/extrinsic/v1"
params = {}
# params['start_block'] = 3302088
# params['end_block']   = 3429944
params['full_name'] = 'SubtensorModule.set_weights'
params['timestamp_start'] = 1736531098
params['timestamp_end'] = 1736792133
params['limit'] = 200
params['page'] = 1
# cycle through the api pages loading a dataframe
while params['page'] is not None: 
    response_json = taostats_API.get_json(endpoint=endpoint,params=params)
    if response_json is not None:
        next_page = response_json['pagination']['next_page']
        total_pages = response_json['pagination']['total_pages']
        page_no = params['page']
        if page_no == 1:
            df = pd.DataFrame(response_json['data'])
        else:
            df = df.append(response_json['data'])
        print(f'loading page no {page_no} of {total_pages}',end='\r')
        params['page'] = next_page
    else:
        params['page'] = None

if response_json is None:
    print(f'No response to get')
    sys.exit()


df_save1 = df.copy(deep=True)

logPath = pathlib.Path.cwd()
api_name_base = 'api_output'
# suffix is last part of full name if it exists
api_name_suffix = params['full_name'].split(".")[-1] if params['full_name'] is not None  else ""
api_name_ext = 'csv'
api_file_output = logPath / f'{api_name_base}{api_name_suffix}.{api_name_ext}'

with api_file_output.open(mode='w') as outfile:
    df_save1.to_csv(outfile, index=False)

debug_marker = 1


