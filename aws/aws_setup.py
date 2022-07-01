#!/usr/bin/python

# this script will create a new bucket and add a user that can interact with it
import sys
import boto3
import json
import os
import secrets
import string
import traceback
from rich.console import Console

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

console = Console()

u_key = sys.argv[1]
u_secret = sys.argv[2]
project_name = sys.argv[3]+"-dxw"

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
    
    print("Start creating resources...")
    aws_resources = {}

    iam = boto3.client("iam",
                    aws_access_key_id=u_key,
                    aws_secret_access_key=u_secret)

    s3 = boto3.client("s3",
                    aws_access_key_id=u_key,
                    aws_secret_access_key=u_secret)

    rds = boto3.client('rds',
			region_name='us-east-1',
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
        bucket_name = (project_name+"-vault").replace("_", "-").lower()
        return(s3.create_bucket(Bucket=bucket_name))

    def create_user(iam, project_name):
        response = iam.create_user(UserName=project_name+"-user")
        return(response)

    def attach_user_policy(iam, policy_arn, username):
        response = iam.attach_user_policy(
            UserName=username,
            PolicyArn=policy_arn
        )

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

    def create_database(rds, project_name):
        db_user = project_name+"-"+''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(8))
        db_password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(50))
        response = rds.create_db_instance(
            AllocatedStorage=5,
            DBInstanceClass='db.t3.micro',
            DBInstanceIdentifier=project_name+"-db",
            Engine='Postgres',
            EngineVersion='13.4',
            MasterUserPassword=db_password,
            MasterUsername=db_user.replace("-", "_"))
        response["DBInstance"]["MasterUserPassword"] = db_password

        print("     - database instance created")
        print("     - waiting for instance to complete initialization ...")

        return(response)

    try:
        user = create_user(iam, project_name)
        aws_resources["user"] = user["User"]
        console.print(" :thumbs_up: user created", style="green")
    except Exception as err:
        print(colored(255,255,0," x user could not be created"))
        console.print(err.message)

    try:
        policy = create_policy(iam, project_name, path)
        aws_resources["policy"] = policy["Policy"]
        console.print(" :thumbs_up: policy created", style="green")
    except Exception as err:
        print(colored(255,255,0," x policy could not be created"))
        console.print(err.message)

    try:
        key = create_access_key(iam, aws_resources["user"]["UserName"])
        aws_resources["user"]["key"] = key
        console.print(" :thumbs_up: user access key created", style="green")
    except Exception as err:
        print(colored(255,255,0," x user access key could not be created"))
        console.print(type(err))
        console.print(err)

    try:
        bucket = create_bucket(s3, project_name)
        aws_resources["bucket"] = bucket
        console.print(" :thumbs_up: S3 bucket created", style="green")
    except Exception as err:
        print(colored(255,255,0," x S3 bucket could not be created"))
        console.print(err, style="red")

    try:
        attach_user_policy(iam, aws_resources["policy"]["Arn"], aws_resources["user"]["UserName"])
        console.print(" :thumbs_up: policy attached to user", style="green")
    except Exception as err:
        print(colored(255,255,0," x user policy could not be attached to user"))
        console.print(err, style="red")

    try:
        attach_cors(s3, aws_resources["bucket"]["Location"].replace("/",""), path)
        console.print(" :thumbs_up: CORS rules attached to S3 bucket", style="green")
    except Exception as err:
        print(colored(255,255,0," x CORS rules could not be attached to S3 bucket"))
        console.print(err, style="red")

    try:
        block_bucket(s3, aws_resources["bucket"]["Location"].replace("/",""))
        console.print(" :thumbs_up: S3 bucket privacy enhanced", style="green")
    except Exception as err:
        print(colored(255,255,0," x S3 bucket privacy could not be enhanced"))
        console.print_exception(show_locals=False)

    try:
        response = create_database(rds, project_name)
        aws_resources["database"] = response["DBInstance"]
        console.print(" :thumbs_up: RDS database created", style="green")
    except Exception as err:
        print(traceback.format_exc())
        print(colored(255,255,0," x RDS database could not be created"))
        console.print_exception(show_locals=False)

    with open(path+'/aws_config_'+project_name+'.json', 'w') as f:
        f.write(json.dumps(aws_resources, indent=4, sort_keys=True, default=str))
