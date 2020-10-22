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
    esres = requests.post(esurl, auth=HTTPBasicAuth('kiyoon2120', 'KIwi727272!'))
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

    client = boto3.client("sns",aws_access_key_id="ASIAVTRHLQ2N56HHBDIA",
    aws_secret_access_key="mGmjjaQSTU0CZPyThE77ZnvlG6qLmtWigtD4MBz4",
    aws_session_token = "FwoGZXIvYXdzEEUaDJ4lZpYpFjY7RNqchiK8AT4ZK68VAl9Qo+7yJ2vdjTVY2ZajpIUVfq98CF/9kPcQ9HLLqz0zR59zpOWw92EeAcEiXxOBzbd9fdcKSbBguvM/oivoAxyPEzssSp92L4lNhpf50EqGjxMpc/03QdJwIA6qV13tZd8kdED/RfcE8agNUMq5wiz7cjUDWBgroFrmiYvT5AIjch1zbz5F+zOq9zssmNA9HhWt6CYPaxDJxadCDfNgScYQ0bw8J6Umk6zhyi5pQztgHlxSvT8gKLOMwvwFMi0jtyfyXT4SnI25BbcAL2hP9vAlif/ZyztbDpHXxPoQvf82h9pYBi3GZtQH3Us=")

    snstext = 'This is my recommendation list.\n' + comments
    response = client.publish(
        PhoneNumber = "+1"+ phone,
        Message = snstext
    )
        