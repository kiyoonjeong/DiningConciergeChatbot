import json
import boto3

client = boto3.client('lex-runtime')

def lambda_handler(event, context):

    response = client.post_text(
        botName = 'restbot',
        botAlias = 'newlex',
        userId = 'kiyoon2120',
        inputText = event["messages"][0]["unstructured"]["text"])
    
    return {
        'statusCode': 200,

        'body': response
    }
