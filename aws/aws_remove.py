import sys
import boto3
import json
from tqdm import trange
import time
import sys
import os
from rich.console import Console
import traceback

project_name = sys.argv[1]

console = Console()

path = os.path.dirname(__file__)

aws_del = {}
try:
    with open(path+"/../secrets/aws_config_"+project_name.lower()+"-dxw.json".lower(), "r") as f:
        aws_del = json.load(f)
except Exception:
    traceback.print_exc()
    print("AWS resource file could not be read")
    quit()

def delete_bucket_completely(s3, bucket_name):
    response = s3.list_objects_v2(
        Bucket=bucket_name,
    )
    while response['KeyCount'] > 0:
        print('Deleting %d objects from bucket %s' % (len(response['Contents']),bucket_name))
        response = s3.delete_objects(
            Bucket=bucket_name,
            Delete={
                'Objects':[{'Key':obj['Key']} for obj in response['Contents']]
            }
        )
        response = s3.list_objects_v2(
            Bucket=bucket_name,
        )
    print('\t\t- empty and delete bucket %s' % bucket_name)
    response = s3.delete_bucket(
        Bucket=bucket_name
    )

def delete_database(rds, aws_del):
    rds.delete_db_instance(
        DBInstanceIdentifier=aws_del['database']['DBInstanceIdentifier'],
        SkipFinalSnapshot=True,
        DeleteAutomatedBackups=True)

def delete_all(iam, ec2, s3, lambda_client, rds, aws_del):
    counter = 0
    error_counter = 0
    try:
        response = iam.detach_user_policy(
            UserName=aws_del["user"]["UserName"],
            PolicyArn=aws_del["policy"]["Arn"]
        )
        counter = counter+1
        console.print(" :thumbs_up: user access key created", style="green")
    except Exception as err:
        console.print(" :x: policy could not be detached", style="bold red")
        print(err.args[0])
        error_counter = error_counter+1

    try:
        respsone = iam.delete_policy(PolicyArn=aws_del["policy"]["Arn"])
        counter = counter+1
        console.print(" :thumbs_up: user policy deleted", style="green")
    except Exception as err:
        console.print(" :x: user policy could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    try:
        response = iam.delete_access_key(
            AccessKeyId=aws_del["user"]["key"]["AccessKeyId"],
            UserName=aws_del["user"]["UserName"]
        )
        counter = counter+1
        console.print(" :thumbs_up: user access key deleted", style="green")
    except Exception as err:
        console.print(" :x: user access key could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    try:
        respsone = iam.delete_user(UserName=aws_del["user"]["UserName"])
        counter = counter+1
        console.print(" :thumbs_up: user deleted", style="green")
    except Exception as err:
        console.print(" :x: user could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    try:
        response = delete_bucket_completely(s3, aws_del["bucket"]["Name"])
        counter = counter+1
        console.print(" :thumbs_up: S3 bucket deleted", style="green")
    except Exception as err:
        console.print(" :x: S3 bucket could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1

    try:
        response = rds.modify_db_instance(
            DBInstanceIdentifier=aws_del['database']['DBInstanceIdentifier'],
            VpcSecurityGroupIds=[]
        )
        console.print(" :thumbs_up: Detach security group.", style="green")
    except Exception as err:
        console.print(" :x: Security group could not be detached", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1

    try:
        ec2.delete_security_group(GroupId=aws_del["security_group"])
        console.print(" :thumbs_up: Deleted security group.", style="green")
    except Exception as err:
        console.print(" :x: Security group could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1

    try:
        response = delete_database(rds, aws_del)
        console.print(" :thumbs_up: RDS database instance deletion started. Takes time to complete.", style="green")
    except Exception as err:
        console.print(" :x: RDS database instance could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    role_name = f'{project_name}-checksum-role'
    
    try:
        lambda_client.delete_function(FunctionName=aws_del["lambda"]["function"])
        console.print(" :thumbs_up: Deleted lambda function", style="green")
    except Exception as e:
        console.print(" :x: Failed to delete lambda function", style="bold red")

    try:
        # Detach policy from the role
        iam.detach_role_policy(RoleName=role_name, PolicyArn=aws_del["lambda"]["policy"])
        iam.delete_policy(PolicyArn=aws_del["lambda"]["policy"])
        console.print(" :thumbs_up: Deleted lambda function policy", style="green")
    except Exception as e:
        console.print(" :x: Failed to delete lambda function policy", style="bold red")

    try:
        iam.delete_role(RoleName=role_name)
        console.print(" :thumbs_up: Deleted lambda function role", style="green")
    except Exception as e:
        console.print(" :x: Failed to delete lambda function role", style="bold red")
    
    print("\nScript completed")
    if error_counter > 0:
        console.print("The script encountered "+str(error_counter)+" errors. Some of the resources might not have been removed or have been removed previously.", style="red")

def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)

print("-"*80)
console.print("[red][bold]WARNING![/bold][/red] Deleting project: [bold]"+project_name+"[/bold]\n")
console.print("!!! You are about to [bold]permanently[/bold] remove all data associated with the project !!!\n")
console.print("The script will delete", style="bright_yellow")
try:
    console.print(" - AWS user:\t "+aws_del["user"]["UserName"], style="bright_yellow")
    console.print(" - S3 bucket:\t "+aws_del["bucket"]["Location"].replace("/", ""), style="bright_yellow")
    console.print(" - RDS database: "+aws_del["database"]["DBInstanceIdentifier"], style="bright_yellow")
except Exception:
    x=1

print("-"*80)
val = input("Remove all resources on AWS (Y/n)? : ")
if val == "Y":
    val = input("Re-enter name of project to delete all accociated resources: ")
    if val == project_name:
        for i in trange(100, desc="Countdown ", bar_format="{desc:<5} |{bar}", leave=False):
            time.sleep(0.02)
        print("Deleting resources.\n")
        iam = boto3.client("iam", region_name=aws_del["aws_region"])
        ec2 = boto3.client("ec2", region_name=aws_del["aws_region"])
        s3 = boto3.client("s3", region_name=aws_del["aws_region"])
        lambda_client = boto3.client("lambda", region_name=aws_del["aws_region"])
        rds = boto3.client("rds", region_name=aws_del["aws_region"])       
        delete_all(iam, ec2, s3, lambda_client, rds, aws_del)
