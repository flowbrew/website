import json
import boto3
from botocore.exceptions import ClientError


def email(addr, subject, body):
    SENDER = "Checkout Bot <checkout@flowbrew.ru>"
    RECIPIENT = addr
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

    addr = (
        "bot@flowbrew.ru"
        if params['email'].strip() == 'bot@flowbrew.ru' else 
        "ak@flowbrew.ru"
    )

    if not email(addr, subject, body):
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
