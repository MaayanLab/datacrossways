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
import zipfile

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

    lambda_client = boto3.client('lambda', region_name=aws_region)
    
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
    
    def get_instance_id():
        url = "http://169.254.169.254/latest/api/token"
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        TOKEN = requests.put(url, headers=headers).text
        headers = {"X-aws-ec2-metadata-token": TOKEN}
        url = "http://169.254.169.254/latest/meta-data/instance-id"
        response = requests.get(url, headers=headers)
        ip = response.text
        url = "http://169.254.169.254/latest/meta-data/placement/availability-zone"
        response = requests.get(url, headers=headers)
        aws_region = response.text[:-1]
        return (ip, aws_region)

    def get_instance_ips(instance_id: str, instance_region):
        ec2_temp = boto3.client("ec2", region_name=instance_region)
        data = ec2_temp.describe_instances(Filters=[{"Name": "instance-id", "Values": [instance_id]}])
        private_ip = data["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
        public_ip = data["Reservations"][0]["Instances"][0]["PublicIpAddress"]
        return (private_ip, public_ip)
    
    def create_security_group(ec2, group_name, description):
        instance_id, availability_zone = get_instance_id()
        public_ip, private_ip = get_instance_ips(instance_id, availability_zone)
        response = ec2.create_security_group(
            GroupName=group_name,
            Description=description
        )
        security_group_id = response['GroupId']
        print('Security Group Created %s for IP %s.' % (security_group_id, public_ip))
        ip_permissions = [
                {'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [{'CidrIp': public_ip+"/32", 'Description': 'postgresql access'}]}
            ]
        if len(private_ip) > 0:
            ip_permissions.append(
                {'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [{'CidrIp': private_ip+"/32", 'Description': 'postgresql access'}]}
            )
        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=ip_permissions
        )
        return security_group_id

    def create_checksum_lambda_function(iam, s3, lambda_client, project_name, path, aws_resources):
        aws_resources["lambda"] = {}

        try:
            assume_role_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            role_response = iam.create_role(
                RoleName=f'{project_name}-checksum-role',
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
            )
            role_arn = role_response['Role']['Arn']
            aws_resources["lambda"]["role"] = role_arn
        except Exception:
            xx = 0
        
        try:
            # Define the policy JSON
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:GetObject",
                            "s3:PutObjectTagging"
                        ],
                        "Resource": f"arn:aws:s3:::{project_name}-vault/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*"
                    }
                ]
            }

            # Create the policy
            policy_response = iam.create_policy(
                PolicyName=f'{project_name}-checksum-policy',
                PolicyDocument=json.dumps(policy_document)
            )

            # Get the ARN of the new policy
            policy_arn = policy_response['Policy']['Arn']
            aws_resources["lambda"]["policy"] = policy_arn
        except Exception:
            xx = 0

        try:
            # Attach the policy to the role
            attachment_response = iam.attach_role_policy(
                RoleName=f'{project_name}-checksum-role',
                PolicyArn=policy_arn
            )

            with zipfile.ZipFile('/tmp/lambda_function.zip', 'w') as z:
                z.write(path+'/checksum.py', compress_type=zipfile.ZIP_DEFLATED)

            # Read the zipped code
            with open('/tmp/lambda_function.zip', 'rb') as f:
                zipped_code = f.read()

            # Create the Lambda function
            response = lambda_client.create_function(
                FunctionName=f'{project_name}-checksum-function',
                Runtime='python3.11',
                Role=role_arn,
                Handler='checksum.lambda_handler',
                Code={
                    'ZipFile': zipped_code
                },
                Description=f'A lambda function triggered by S3 bucket {project_name}-vault to compute checksum once file is created',
                Timeout=15,
                MemorySize=128
            )
            lambda_arn = response['FunctionArn']
            aws_resources["lambda"]["function"] = lambda_arn
        except Exception:
            xx = 0
        
        # Grant permission to S3 to invoke the Lambda function
        lambda_client.add_permission(
            FunctionName='ihdh-checksum-function',
            StatementId='AllowS3Invoke',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{project_name}-vault'
        )

        # Add S3 trigger to Lambda function
        s3.put_bucket_notification_configuration(
            Bucket=f"{project_name}-vault",
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': lambda_arn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        return 1

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
        create_checksum_lambda_function(iam, s3, lambda_client, project_name, path, aws_resources)
        console.print(" :thumbs_up: checksum lambda function created", style="green")
    except Exception as err:
        console.print(" :x: Checksum lambda function could not be created", style="bold red")
        print(err)
    
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
