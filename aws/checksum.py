'''
This is the lambda function that computed the the sha256 checksum 
for every file that gets uploaded to a specified bucket. The lambda 
function result is attached to a field in the meta data of S3 under 
checksum.
'''

import boto3
import hashlib
import urllib.parse

s3 = boto3.client('s3')

def calculate_sha256(streaming_body, block_size=65536):
    sha256 = hashlib.sha256()
    for block in iter(lambda: streaming_body.read(block_size), b''):
        sha256.update(block)
    return sha256.hexdigest()

def lambda_handler(event, context):
    # Get bucket name and key from the Lambda event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Get the object from S3
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    # Get the streaming body
    streaming_body = obj['Body']
    
    # Calculate checksum
    checksum = calculate_sha256(streaming_body)

    # URL-encode the key for CopySource
    encoded_key = urllib.parse.quote(key)
    
    # Add the checksum as metadata to the S3 object
    s3.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': encoded_key}, Key=key, 
                   Metadata={'checksum': checksum}, MetadataDirective='REPLACE')
   
    return {
        'statusCode': 200,
        'body': 'SHA-256 checksum successfully calculated and added as metadata.'
    }