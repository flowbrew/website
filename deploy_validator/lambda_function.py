import json
import boto3
from botocore.exceptions import ClientError
import requests


def lambda_handler(event, context):
    params = json.loads(event.get("body", dict()))

    headers = {
        'User-Agent': 'Github Action',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
    }

    return {
        'statusCode': 200,
        'body': requests.get(params['url'], headers=headers).text,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        }
    }
