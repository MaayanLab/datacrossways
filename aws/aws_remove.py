import sys
import boto3
import json
from tqdm import trange
import time
import sys
import os
from rich.console import Console

u_key = sys.argv[1]
u_secret = sys.argv[2]
project_name = sys.argv[3]

console = Console()

path = os.path.dirname(__file__)

aws_del = {}
try:
    with open(path+"/../secrets/aws_config_"+project_name+"-dxw.json", "r") as f:
        aws_del = json.load(f)
except Exception:
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
    print('Now deleting bucket %s' % bucket_name)
    response = s3.delete_bucket(
        Bucket=bucket_name
    )

def delete_database(rds, aws_del):
    rds.delete_db_instance(
        DBInstanceIdentifier=aws_del['database']['DBInstanceIdentifier'],
        SkipFinalSnapshot=True,
        DeleteAutomatedBackups=True)

def delete_all(iam, s3, rds, aws_del):
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
        console.print(" :x: policy detached", style="bold red")
        print(err.args[0])
        error_counter = error_counter+1

    try:
        respsone = iam.delete_policy(PolicyArn=aws_del["policy"]["Arn"])
        counter = counter+1
        console.print(" :thumbs_up: user policy deleted", style="green")
    except Exception:
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
    except Exception:
        console.print(" :x: user access key could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    try:
        respsone = iam.delete_user(UserName=aws_del["user"]["UserName"])
        counter = counter+1
        console.print(" :thumbs_up: user deleted", style="green")
    except Exception:
        console.print(" :x: user could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    try:
        response = delete_bucket_completely(s3, aws_del["bucket"]["Location"].replace("/",""))
        counter = counter+1
        console.print(" :thumbs_up: S3 bucket deleted", style="green")
    except Exception:
        console.print(" :x: S3 bucket could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1

    try:
        response = delete_database(rds, aws_del)
        console.print(" :thumbs_up: RDS database instance deleted", style="green")
    except Exception:
        console.print(" :x: RDS database instance could not be deleted", style="bold red")
        print(err.args[0]) 
        error_counter = error_counter+1
    
    print("\nScript completed")
    if error_counter > 0:
        console.print("The script encountered "+str(error_counter)+" errors. Some of the resources might not have been removed or have been removed previously.", style="red")

def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)

print("-"*80)
console.print("[red]WARNING![/red] Deleting project: [bold]"+project_name+"[/bold]")
console.print("!!! You are about to [bold]permanently[/bold] remove all data associated with the project !!!\n")
console.print("The script will delete", style="bright_yellow")
console.print(" - AWS user:\t"+aws_del["user"]["UserName"], style="bright_yellow")
console.print(" - S3 bucket:\t"+aws_del["bucket"]["Location"].replace("/", ""), style="bright_yellow")
console.print(" - RDS database: "+aws_del["database"]["Database"], style="bright_yellow")
print("-"*80)
val = input("Remove all resources on AWS (Y/n)? : ")
if val == "Y":
    val = input("Re-enter name of project to delete all accociated resources: ")
    if val == project_name:
        for i in trange(100, desc="Countdown ", bar_format="{desc:<5} |{bar}", leave=False):
            time.sleep(0.02)
        print("Deleting resources.\n")
        iam = boto3.client("iam",
                aws_access_key_id=u_key,
                aws_secret_access_key=u_secret)
        s3 = boto3.client("s3",
                aws_access_key_id=u_key,
                aws_secret_access_key=u_secret)
        rds = boto3.client("rds",
                region_name='us-east-1',
                aws_access_key_id=u_key,
                aws_secret_access_key=u_secret)       
        delete_all(iam, s3, rds, aws_del)
