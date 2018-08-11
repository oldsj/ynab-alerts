import requests

from os import environ

PAT = environ.get('PAT')

BUDGET_ID = '88d9f117-21ac-4ae9-9470-374eb9d62712'
SHOPPING_ID = '659cc7d0-e243-40a3-b343-133965f46232'
YNAB_API = 'https://api.youneedabudget.com/v1'

headers = {
'accept': 'application/json',
'Authorization': f'Bearer {PAT}'
}

shopping = requests.get(f'{YNAB_API}/budgets/{BUDGET_ID}/categories/{SHOPPING_ID}', 
                    headers=headers)

activity = 250000
#activity = shopping.json()['data']['category']['activity']
balance = shopping.json()['data']['category']['balance']

remaining_percent = int(round(100 - (100 * (activity / balance))))

alert_threshold = 25
if(remaining_percent < alert_threshold):
    print(remaining_percent)