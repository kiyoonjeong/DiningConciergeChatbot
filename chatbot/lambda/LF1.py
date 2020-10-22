import json
import pprint
from botocore.vendored import requests
import sys
import urllib
from datetime import datetime
import dateutil
import math
import boto3
import logging
import os
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    return dispatch(event)

def dispatch(intentRequest):
    intentName = intentRequest['currentIntent']['name']
    
    # Dispatch to your bot's intent handlers
    if intentName == 'GreetingIntent':
        return greetingIntent(intentRequest)
    elif intentName == 'DininSuggestionsIntent':
        return diningSuggestionIntent(intentRequest)
    elif intentName == 'ThankYouIntent':
        return thankYouIntent(intentRequest)
    else:
        return
    
def greetingIntent(intentRequest):
    return {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': "Fulfilled",
            'message': {
                'contentType': 'PlainText', 
                'content': 'Hi! Please enter \'restaurant\' to start. '}
        }
    }
    
def thankYouIntent(intentRequest):
    return {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled',
            'message': {
                'contentType': 'PlainText', 
                'content': 'Thank you. Hope you enjoy your meal!'}
        }
    }    


def diningSuggestionIntent(intentRequest):
    
    location = getSlot(intentRequest)["Location"]
    cuisine = getSlot(intentRequest)["cuisine"]
    partysize = getSlot(intentRequest)["partysize"]
    date = getSlot(intentRequest)["date"]
    phone = getSlot(intentRequest)["phone"]
    
    source = intentRequest['invocationSource']
    if source == 'DialogCodeHook':
        slots = getSlot(intentRequest)
        
        validationResult = validateUInputs(location, cuisine, partysize, date, phone)
        
        if not validationResult['isValid']:
            slots[validationResult['violatedSlot']] = None
            
            return elicitSlot(intentRequest['sessionAttributes'],
                               intentRequest['currentIntent']['name'],
                               slots,
                               validationResult['violatedSlot'],
                               validationResult['message'])
                               
        outputSessionAttributes = intentRequest['sessionAttributes'] if intentRequest['sessionAttributes'] is not None else {}
        
        return delegate(outputSessionAttributes, getSlot(intentRequest))
    
    user_input = {
                    "Location":location,
                    "cuisine":cuisine,
                    "partysize":partysize,
                    "date": date,
                    "phone": phone,
            }
                
    messageId = sendSqs(user_input)
    
    return {
        'dialogAction': {
            'type': "ElicitIntent",
            'message': {
                'contentType': 'PlainText', 
                'content': 'Here is my recommend list.'}
        }
    }    
    
def getSlot(intentRequest):
    return intentRequest['currentIntent']['slots']    
    

def isValidDate(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def formatReturnMessage(pIsValid, pFailedSlot, pMessage):
    if pMessage is None:
        return {
            "isValid": pIsValid,
            "violatedSlot": pFailedSlot
        }

    return {
        'isValid': pIsValid,
        'violatedSlot': pFailedSlot,
        'message': {'contentType': 'PlainText', 'content': pMessage}
    } 

def validateUInputs(loc, cuisine, partysize, ddate, phone):
    
    locations = ['newyork', 'manhattan', 'brooklyn']
    if loc is not None and loc.lower() not in locations:
        return formatReturnMessage(False,
                                    'Location',
                                    'Please enter locations in New York. Pick one of these : newyork, manhattan, brooklyn')  

    cuisines = ['french', 'chinese', 'italian','newamerican', 'japanese']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return formatReturnMessage(False,
                                    'cuisine',
                                    'Pick one of these : newamerican, japanese, italian, french, chinese')                                      

    if partysize is not None:
        partysize = int(partysize)
        if partysize > 10 or partysize < 0:
            return formatReturnMessage(False,
                                      'partysize',
                                      'You can only reserve for 1 to 10 seatings at a time.')    

    currdate = str(datetime.now()).split()
    
    if ddate is not None:
        if not isValidDate(ddate):
            return formatReturnMessage(False, 'date', 'Please use a valid date format.')
        if currdate[0] > str(ddate):
            return formatReturnMessage(False, 'date', 'Please enter valid date.')   

    if phone is not None :
        if len(phone) != 10 :
             return formatReturnMessage(False, 'phone', 'Please enter 10 digit phone number ex) 6667778888') 
                                       
    return formatReturnMessage(True, None, None)    
    

def elicitSlot(SessionAttributes, IntentName, Slots, SlotsToElicit, Message):
    return {
        'sessionAttributes': SessionAttributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': IntentName,
            'slots': Slots,
            'slotToElicit': SlotsToElicit,
            'message': Message
        }
    }

def delegate(SessionAttributes, Slots):
    return {
        'sessionAttributes': SessionAttributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': Slots
        }
    }



def sendSqs(pData):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='restqueue')
    queue_url = queue.url
    messageAttributes = {
        'Location': {
            'DataType': 'String',
            'StringValue': pData['Location']
        },
        'cuisine': {
            'DataType': 'String',
            'StringValue': pData['cuisine']
        },
        'date': {
            'DataType': 'String',
            'StringValue': pData['date']
        },
        'partysize': {
            'DataType': 'String',
            'StringValue': pData['partysize']
        },
        'phone': {
            'DataType': 'String',
            'StringValue': pData['phone']
        },
    }
    
    messageBody=('Restaurant Recommendation')
    
    response = queue.send_message(
        MessageAttributes = messageAttributes,
        MessageBody = messageBody
        )

    return response.get('MessageId')