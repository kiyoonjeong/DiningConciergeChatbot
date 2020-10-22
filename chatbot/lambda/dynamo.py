from __future__ import print_function
import boto3
import json
import decimal
from datetime import datetime
import requests

#japanese-japanese, chinese -chinese, french -french, american - newamerican, italian - italian
cuisinetype = 'french'


API_KEY = 'PKzqesxHVm8yVBWXjlz2jS8FDi9n-knRtobJb7sqQYPOEqRElBQ5S6Z5vEC0Y3DKhHNdXdEtAtnvnTrGQx3JnUkuQGC-bRfND1nrW-Rbvu2n-BsiOZ3RknmBsiiNX3Yx'
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'bearer %s' % API_KEY}

PARAMETERS = {'term': 'restaurant',
             'limit': 50,
             'offset': 0,
             'radius': 10000,
             'categories': cuisinetype,
             'location': 'Manhattan'}

for _ in range(20):
    response = requests.get(url = ENDPOINT,
                            params = PARAMETERS,
                            headers = HEADERS)
    restaurant_data = response.json()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')
    i=0
    for resta in restaurant_data['businesses']:
         BusinessID = resta['id']
         Cuisine = cuisinetype
         Name = resta['name']
         if len(resta['location']['display_address']) < 2:
             print("exception")
             Address = resta['location']['display_address'][0]
         else:
            Address = resta['location']['display_address'][0]  + ' ' + resta['location']['display_address'][1]
         Coordinates = str(resta['coordinates']['latitude']) + ' ' + str(resta['coordinates']['longitude'])
         NumberofReviews = str(resta['review_count'])
         Rating = str(resta['rating'])
         ZipCode = str(resta['location']['zip_code'])
         now = datetime.now()
         current_time = now.strftime("%m-%d-%Y %H:%M:%S")
         InsertedAtTimestamp = current_time
    
         item = {
             'rid': BusinessID,
             'Cuisine': Cuisine,
             'Name': Name,
             'Address': Address,
             'Coordinates': Coordinates,
             'NumberofReviews': NumberofReviews,
             'Rating': Rating,
             'ZipCode': ZipCode,
             'InsertionTimeStamp': InsertedAtTimestamp,
         }
    
         response = table.put_item(Item=item)
    PARAMETERS['offset'] += 50
     
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }