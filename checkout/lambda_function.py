import json
import boto3
from botocore.exceptions import ClientError


def email(subject, body):
    SENDER = "Checkout Bot <checkout@flowbrew.ru>"
    RECIPIENT = "ak@flowbrew.ru"
    AWS_REGION = "us-east-1"
    CHARSET = "UTF-8"

    client = boto3.client('ses', region_name=AWS_REGION)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': body,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
        return False
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return True


def lambda_handler(event, context):
    params = json.loads(event.get("body", dict()))

    subject = 'Новый заказ от ' + params.get('name', '???')
    params_str = '\n'.join(f'{k} = {v}' for k, v in params.items())
    body = 'Получен новый заказ!\n\n' + params_str

    if not email(subject, body):
        return {
            'statusCode': 500,
            'body': json.dumps({'result': 'error'}),
            'headers': {
                'Access-Control-Allow-Origin': '*',
            }
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'result': 'ok'}),
        'headers': {
            'Access-Control-Allow-Origin': '*',
        }
    }
