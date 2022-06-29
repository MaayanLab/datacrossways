#!/usr/bin/python

# this script will create a new bucket and add a user that can interact with it
import sys
import boto3
import json
import os

u_key = sys.argv[1]
u_secret = sys.argv[2]
project_name = sys.argv[3]

path = os.path.dirname(__file__)

if "_" in project_name:
    print("Project name cannot contain underscores.")
elif " " in project_name:
    print("Project name cannot contain spaces.")
elif "." in project_name:
    print("Project name cannot contain periods.")
elif "," in project_name:
    print("Project name cannot contain commas.")
else:

    aws_resources = {}

    iam = boto3.client("iam",
                    aws_access_key_id=u_key,
                    aws_secret_access_key=u_secret)

    s3 = boto3.client("s3",
                    aws_access_key_id=u_key,
                    aws_secret_access_key=u_secret)
    
    def colored(r, g, b, text):
        return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)

    def list_users(iam):
        paginator = iam.get_paginator('list_users')
        for response in paginator.paginate():
            for user in response["Users"]:
                print(f"Username: {user['UserName']}, Arn: {user['Arn']}")

    def create_policy(iam, project_name, path):
        f = open(path+"/bucket_policy_template.json")
        policy = json.load(f)
        f.close()
        for s in policy["Statement"]:
            s["Resource"][0] = "arn:aws:s3:::"+project_name+"-vault/*"
        response = iam.create_policy(
            PolicyName=project_name+"-bucket-permission",
            PolicyDocument=json.dumps(policy)
        )
        return(response)

    def create_bucket(s3, project_name):
        bucket_name = (project_name+"-vault").replace("_", "-")
        return(s3.create_bucket(Bucket=bucket_name))

    def create_user(iam, project_name):
        response = iam.create_user(UserName=project_name+"-user")
        return(response)

    def attach_user_policy(iam, policy_arn, username):
        response = iam.attach_user_policy(
            UserName=username,
            PolicyArn=policy_arn
        )
        print(response)

    def create_access_key(iam, username):
        response = iam.create_access_key(
            UserName=username
        )
        return(response['AccessKey'])

    def attach_cors(s3, bucket, path):
        f = open(path+"/bucket_cors_template.json")
        cors_configuration = json.load(f)
        f.close()
        response = s3.put_bucket_cors(Bucket=bucket,
                    CORSConfiguration=cors_configuration)
        print(response)

    def block_bucket(s3, bucket):
        response = s3.put_public_access_block(
                    Bucket=bucket,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
        return(response)

    try:
        user = create_user(iam, project_name)
        aws_resources["user"] = user["User"]
        print(colored(0,255,0," - user created"))
    except Exception:
        print(colored(255,255,0," - user already exists"))

    try:
        policy = create_policy(iam, project_name, path)
        aws_resources["policy"] = policy["Policy"]
        print(colored(0,255,0," - policy created"))
    except Exception:
        print(colored(255,255,0," - policy could not be created"))

    try:
        key = create_access_key(iam, aws_resources["user"]["UserName"])
        aws_resources["user"]["key"] = key
        print(colored(0,255,0," - user access key created"))
    except Exception:
        print(colored(255,255,0," - user access key could not be created"))

    try:
        bucket = create_bucket(s3, project_name)
        aws_resources["bucket"] = bucket
        print(colored(0,255,0," - bucket created"))
    except Exception:
        print(colored(255,255,0," - S3 bucket could not be created"))

    try:
        attach_user_policy(iam, aws_resources["policy"]["Arn"], aws_resources["user"]["UserName"])
        print(colored(0,255,0," - policy attached to user"))
    except Exception:
        print(colored(255,255,0," - upolicy could not be attached to user"))

    try:
        attach_cors(s3, aws_resources["bucket"]["Location"].replace("/",""), path)
        print(colored(0,255,0," - CORS rules attached to S3 bucket"))
    except Exception:
        print(colored(255,255,0," - CORS rules could not be attached to S3 bucket"))

    try:
        block_bucket(s3, aws_resources["bucket"]["Location"].replace("/",""))
        print(colored(0,255,0," - bucket privacy enhanced"))
    except Exception:
        print(colored(255,255,0," - S3 bucket privacy could not be enhanced"))

    with open(path+'/aws_config_'+project_name+'.json', 'w') as f:
        f.write(json.dumps(aws_resources, indent=4, sort_keys=True, default=str))
