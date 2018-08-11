import requests
import boto3
import yaml
from os import environ

def entry(event, context):
    pat = environ['PAT']
    budget_id = '88d9f117-21ac-4ae9-9470-374eb9d62712'
    ynab_api = 'https://api.youneedabudget.com/v1'

    headers = {
    'accept': 'application/json',
    'Authorization': f'Bearer {pat}'
    }

    categories = requests.get(f'{ynab_api}/budgets/{budget_id}/categories', headers=headers)
    category_groups = categories.json()['data']['category_groups']

    # The threshold at which an alert is sent 
    # when the balance for the category drops
    # below this percentage for the budgeted amount
    alert_threshold_percent = 75

    monitor_categories = ['True Expenses', 'Just for Fun']
    for category_group in category_groups:
        if category_group['name'] in monitor_categories:
            group_categories = category_group['categories']

            for category in group_categories:
                category_budgeted = category['budgeted']
                if category_budgeted != 0:
                    # category activity is reported as a negative number, multiply by -1 to flip to positive
                    category_activity = -1 * category['activity']

                    budget_spent_percent = int(100 * (category_activity / category_budgeted))

                    if(budget_spent_percent > alert_threshold_percent):
                        notify_sms("Whoa pump the breaks!\nThe " + 
                                    category['name'] + 
                                    " budget is at " + str(budget_spent_percent)+ 
                                    " percent.")

    response = {
        "statusCode": 200,
        "body": "executed successfully"
    }
    # send the response if triggered by http request
    return response

def notify_sms(message):
    with open('./phone_numbers.yml') as fp:
        phone_numbers = yaml.load(fp)

    client = boto3.client('sns')
    for phone_number in phone_numbers:
        client.publish(
            PhoneNumber = phone_number,
            Message = message
        )
