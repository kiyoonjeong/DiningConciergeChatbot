import json
import boto3
import requests
from requests.auth import HTTPBasicAuth

def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    
    queue_url = 'https://sqs.us-east-1.amazonaws.com/105234542199/restqueue'
    
    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    if 'Messages' not in response:
        print("No message")
        return
    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']
    
    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    
    values = message['MessageAttributes']
    
    location = values['Location']['StringValue']
    cuisine = values['cuisine']['StringValue']
    partysize = values['partysize']['StringValue']
    date = values['date']['StringValue']
    phone = values['phone']['StringValue']
    
    esurl = 'https://search-yelpes-jhmbbuw2jtnxuqagundoslagmy.us-east-1.es.amazonaws.com/_search?q=' + cuisine
    esres = requests.post(esurl, auth=HTTPBasicAuth('*', '*'))
    estext = esres.json()
    
    dynamodb = boto3.resource('dynamodb')
    dbtable = dynamodb.Table('yelp-restaurants')
    
    comments = ""
    count = 1
    for element in estext["hits"]["hits"]:
        if count == 4:
            break
        dbdata = dbtable.get_item(Key = {
            'rid': element["_source"]["rid"]
        })
        item = dbdata['Item']
        comments += str(count)+". " + item['Name'] +" (Location : " + item['Address'] +", Zipcode : " + item['ZipCode']
        comments += ", Coordinates : " + item['Coordinates'] + ", Number of Reviews : " + item['NumberofReviews'] + ", Rating : " + item['Rating'] + ")\n"
        count += 1

    client = boto3.client("sns",aws_access_key_id="*",
    aws_secret_access_key="*",
    aws_session_token = "*",
    snstext = 'This is my recommendation list.\n' + comments
    response = client.publish(
        PhoneNumber = "+1"+ phone,
        Message = snstext
    )
        
