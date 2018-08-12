import requests
import boto3
import yaml
from os import environ

def entry(event, context):
    pat = get_secret('PAT')
    budget_id = '88d9f117-21ac-4ae9-9470-374eb9d62712'
    ynab_api = 'https://api.youneedabudget.com/v1'

    headers = {
    'accept': 'application/json',
    'Authorization': f'Bearer {pat}'
    }

    dynamodb = boto3.resource('dynamodb')
    table_name = environ['DYNAMODB_TABLE']
    table = dynamodb.Table(table_name)

    categories = requests.get(f'{ynab_api}/budgets/{budget_id}/categories', headers=headers)
    category_groups = categories.json()['data']['category_groups']

    # An alert is sent 
    # when the account activity for the category
    # reaches this percentage of the budgeted amount
    alert_threshold_percent = 75

    monitor_categories = ['True Expenses', 'Just for Fun']
    for category_group in category_groups:
        if category_group['name'] in monitor_categories:
            group_categories = category_group['categories']

            for category in group_categories:
                category_budgeted = category['budgeted']
                category_name = category['name']
                # First check if this is a category that has a budget set
                if category_budgeted > 0:
                    try:
                        dynamo_response = table.get_item(
                            Key={'id': category_name}
                        )
                        item = dynamo_response['Item']
                        alert_state = item['alert_state']

                        # category activity is reported as a negative number, multiply by -1 to flip to positive
                        category_activity = -1 * category['activity']

                        budget_spent_percent = int(100 * (category_activity / category_budgeted))
                        # Next check if we've reached the alert threshold
                        if(budget_spent_percent > alert_threshold_percent):
                            # Finally check if this budget has already passed the alert threshold
                            if not alert_state:
                                notify_sms("Whoa pump the breaks!\nThe " + 
                                    category['name'] + 
                                    " budget is at " + str(budget_spent_percent)+ 
                                    " percent.")
                                # Now update the alert_state as being set
                                table.put_item(
                                    Item={
                                        'id': category_name,
                                        'alert_state': True
                                    }
                                )

                        # If the alert threshold is not currently met, reset the alert state to false
                        else:
                            table.put_item(
                                Item={
                                    'id': category_name,
                                    'alert_state': False
                                }
                            )

                    except KeyError:
                        # If the database is missing the key, set alert_state to false initially
                        print("Error key not found.")
                        table.put_item(
                            Item={
                                'id': category_name,
                                'alert_state': False
                            }
                        )

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

def get_secret(key):
    client = boto3.client('ssm')
    resp = client.get_parameter(
        Name=key,
        WithDecryption=True
    )
    return resp['Parameter']['Value']