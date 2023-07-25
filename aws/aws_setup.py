#!/usr/bin/python

# this script will create a new bucket and add a user that can interact with it
import sys
import boto3
import json
import os
import secrets
import string
import time
from rich.console import Console
import traceback
import requests

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

console = Console()

if len(sys.argv) < 2:
    console.print("Usage: python script.py <project_name> [aws_region]", style="bold red")
    sys.exit(1)

project_name = sys.argv[1] + "-dxw"

# Set the AWS region from the command-line argument or use default "us-east-1"
aws_region = sys.argv[2] if len(sys.argv) >= 3 else "us-east-1"

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
    aws_resources["aws_region"] = aws_region

    iam = boto3.client("iam")

    ec2 = boto3.client("ec2", region_name=aws_region)

    s3 = boto3.client("s3", region_name=aws_region)

    rds = boto3.client('rds', region_name=aws_region)
    
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

    def create_bucket(s3, project_name, region="us-east-1"):
        bucket_name = (project_name+"-vault").replace("_", "-").lower()
        if region != "us-east-1":
            bucket_configuration = {
                'LocationConstraint': region,  # Set to the region where the bucket should be created
            }
            return(s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=bucket_configuration))
        else:
            return(s3.create_bucket(Bucket=bucket_name))
    
    def get_bucket_region(s3, project_name):
        response = s3.get_bucket_location(Bucket=project_name+"-vault")        
        region = "us-east-1"
        try:
            region = response["ResponseMetadata"]["LocationConstraint"]
            region = "us-east-1" if region is None else region
        except Exception:
            region = "us-east-1"
        return(region)

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

    def create_database(rds, project_name, security_group_id):
        db_user = project_name+"-"+''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(8))
        db_password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(50))
        response = rds.create_db_instance(
            AllocatedStorage=5,
            DBInstanceClass='db.t3.micro',
            DBInstanceIdentifier=project_name+"-db",
            Engine='Postgres',
            EngineVersion='15.3',
            MasterUserPassword=db_password,
            MasterUsername=db_user.replace("-", "_"),
            VpcSecurityGroupIds=[security_group_id])
        response["DBInstance"]["MasterUserPassword"] = db_password
        print("     - RDS database instance created")
        with console.status(" - waiting for RDS instance to complete initialization ... ", spinner="monkey"):
            time.sleep(20)
            for i in range(100):
                if i > 99:
                    raise Exception("RDS instance timed out during initialization.")
                time.sleep(5)
                resp = rds.describe_db_instances(DBInstanceIdentifier=response["DBInstance"]["DBInstanceIdentifier"])
                if resp["DBInstances"][0]["DBInstanceStatus"] != "creating":
                    dbhost = resp["DBInstances"][0]["Endpoint"]["Address"]
                    response["DBInstance"]["Endpoint"]={"Address": dbhost}
                    break
        return(response)

    def get_public_ip():
        response = requests.get('https://api.ipify.org')
        return response.text

    def create_security_group(ec2, group_name, description):
        ip = get_public_ip()
        response = ec2.create_security_group(
            GroupName=group_name,
            Description=description
        )
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' % (security_group_id, ip))
        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [{'CidrIp': ip+"/32", 'Description': 'postgresql access'}]}
            ]
        )
        return security_group_id


    try:
        user = create_user(iam, project_name)
        aws_resources["user"] = user["User"]
        console.print(" :thumbs_up: user created", style="green")
    except Exception as err:
        console.print(" :x: user could not be created", style="bold red")
        print(err.args[0]) 

    try:
        policy = create_policy(iam, project_name, path)
        aws_resources["policy"] = policy["Policy"]
        console.print(" :thumbs_up: policy created", style="green")
    except Exception as err:
        console.print(" :x: policy could not be created", style="bold red")
        print(err.args[0]) 

    try:
        key = create_access_key(iam, aws_resources["user"]["UserName"])
        aws_resources["user"]["key"] = key
        console.print(" :thumbs_up: user access key created", style="green")
    except Exception as err:
        console.print(" :x: user access key could not be created", style="bold red")

    try:
        bucket = create_bucket(s3, project_name, aws_region)
        bucket["Region"] = aws_region
        bucket["Name"] = project_name+"-vault"
        aws_resources["bucket"] = bucket
        console.print(" :thumbs_up: S3 bucket created", style="green")
    except Exception as err:
        console.print(" :x: S3 bucket could not be created", style="bold red")
        print(err.args[0]) 

    try:
        attach_user_policy(iam, aws_resources["policy"]["Arn"], aws_resources["user"]["UserName"])
        console.print(" :thumbs_up: policy attached to user", style="green")
    except Exception as err:
        console.print(" :x: user policy could not be attached to user", style="bold red")

    try:
        attach_cors(s3, project_name+"-vault", path)
        console.print(" :thumbs_up: CORS rules attached to S3 bucket", style="green")
    except Exception as err:
        console.print(" :x: CORS rules could not be attached to S3 bucket", style="bold red")
        print(err.args[0])

    try:
        block_bucket(s3, project_name+"-vault")
        console.print(" :thumbs_up: S3 bucket privacy enhanced", style="green")
    except Exception as err:
        console.print(" :x: S3 bucket privacy could not be enhanced", style="bold red")
        print(err.args[0])
    
    try:
        security_group = create_security_group(ec2, project_name, project_name)
        aws_resources["security_group"] = security_group
        console.print(" :thumbs_up: Database firewall configured", style="green")
    except Exception as err:
        console.print(" :x: Database firewall configuration failed", style="bold red")
        print(err.args[0])
    
    try:
        response = create_database(rds, project_name, security_group)
        aws_resources["database"] = response["DBInstance"]
        aws_resources["database"]["user"] = aws_resources["database"]["MasterUsername"]
        aws_resources["database"]["pass"] = aws_resources["database"]["MasterUserPassword"]
        aws_resources["database"]["server"] = aws_resources["database"]["Endpoint"]["Address"]
        aws_resources["database"]["port"] = "5432"
        aws_resources["database"]["name"] = "datacrossways"
        db = psycopg2.connect(
                    user=aws_resources["database"]["user"], 
                    password=aws_resources["database"]["pass"], 
                    dbname="postgres", 
                    host=aws_resources["database"]["server"])
        
        db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        db.cursor().execute("CREATE DATABASE datacrossways")
        db.commit()
        db.close()
        console.print(" :thumbs_up: RDS database created", style="green")
    except Exception as err:
        console.print(" :x: RDS database could not be created", style="bold red")
        traceback.print_exc()
        print(err.args[0])

    os.makedirs(path+'/../secrets', exist_ok=True)
    with open(path+'/../secrets/aws_config_'+project_name+'.json'.lower(), 'w') as f:
        f.write(json.dumps(aws_resources, indent=4, sort_keys=True, default=str))
