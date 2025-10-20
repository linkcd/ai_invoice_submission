import json
import time
import boto3

DEBUG = False

def log(data):
    if DEBUG:
        if type(data) is dict:
            text = json.dumps(data, indent=4)
        else:
            text = str(data)
        print(text)

def get_aws_account_id() -> str:
    sts = boto3.client('sts')
    return sts.get_caller_identity().get('Account')

def get_json_object_from_s3_uri(s3_uri) -> dict:
    s3 = boto3.client('s3')
    s3_uri_split = s3_uri.split('/')
    bucket = s3_uri_split[2]
    key = '/'.join(s3_uri_split[3:])
    object_content = s3.get_object(Bucket=bucket, Key=key)['Body'].read()
    return json.loads(object_content)

def invoke_data_automation(input_s3_uri, output_s3_uri, data_automation_arn, aws_account_id, aws_region) -> dict:
    bda = boto3.client('bedrock-data-automation-runtime', region_name=aws_region)
    params = {
        'inputConfiguration': {
            's3Uri': input_s3_uri
        },
        'outputConfiguration': {
            's3Uri': output_s3_uri
        },
        'dataAutomationConfiguration': {
            'dataAutomationProjectArn': data_automation_arn
        },
        'dataAutomationProfileArn': f"arn:aws:bedrock:{aws_region}:{aws_account_id}:data-automation-profile/us.data-automation-v1"
    }
    
    response = bda.invoke_data_automation_async(**params)
    log(response)
    return response

def wait_for_data_automation_to_complete(invocation_arn, aws_region, loop_time_in_seconds=1) -> dict:
    bda = boto3.client('bedrock-data-automation-runtime', region_name=aws_region)
    while True:
        response = bda.get_data_automation_status(invocationArn=invocation_arn)
        status = response['status']
        if status not in ['Created', 'InProgress']:
            print(f" {status}")
            return response
        print(".", end='', flush=True)
        time.sleep(loop_time_in_seconds)