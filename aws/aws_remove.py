import sys
import boto3
import json
from tqdm import trange
import time
import sys
import os

u_key = sys.argv[1]
u_secret = sys.argv[2]
project_name = sys.argv[3]

path = os.path.dirname(__file__)

aws_del = {}
try:
    with open(path+"/aws_config_"+project_name+"-dxw.json", "r") as f:
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

def delete_all(iam, s3, aws_del):
    counter = 0
    error_counter = 0
    try:
        response = iam.detach_user_policy(
            UserName=aws_del["user"]["UserName"],
            PolicyArn=aws_del["policy"]["Arn"]
        )
        counter = counter+1
        print(colored(0,255,0, " - policy detached"))
    except Exception:
        print(colored(255,255,0, " - policy could not be detached"))
        error_counter = error_counter+1

    try:
        respsone = iam.delete_policy(PolicyArn=aws_del["policy"]["Arn"])
        counter = counter+1
        print(colored(0,255,0, " - policy deleted"))
    except Exception:
        print(colored(255,255,0, " - policy could not be deleted"))
        error_counter = error_counter+1
    
    try:
        response = iam.delete_access_key(
            AccessKeyId=aws_del["user"]["key"]["AccessKeyId"],
            UserName=aws_del["user"]["UserName"]
        )
        counter = counter+1
        print(colored(0,255,0, " - user access key deleted"))
    except Exception:
        print(colored(255,255,0," - user access key could not be deleted"))
        error_counter = error_counter+1
    
    try:
        respsone = iam.delete_user(UserName=aws_del["user"]["UserName"])
        counter = counter+1
        print(colored(0,255,0, " - user deleted"))
    except Exception:
        print(colored(255,255,0," - user could not be deleted"))
        error_counter = error_counter+1
    
    try:
        response = delete_bucket_completely(s3, aws_del["bucket"]["Location"].replace("/",""))
        counter = counter+1
        print(colored(0,255,0, " - S3 bucket deleted"))
    except Exception:
        print(colored(255,255,0," - S3 bucket could not be deleted"))
        error_counter = error_counter+1
    
    print("\nScript completed")
    if error_counter > 0:
        print(colored(255,0,0, "The script encountered "+str(error_counter)+" errors. Some of the resources might not have been removed or have been removed previously."))

def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)

print("-"*80)
print(colored(255, 0, 0, "\033[1mWARNING\033[0m") + "Deleting project: \033[1m"+project_name+"\033[0m\n")
print(colored(255, 0, 0, "!!! You are about to \033[1mpermanently\033[0m")+colored(255,0,0, "remove all data associated with the project !!!\n"))
print(colored(255, 255, 0, "The script will delete"))
print(colored(255, 255, 0, " - AWS user:\t")+aws_del["user"]["UserName"])
print(colored(255, 255, 0, " - S3 bucket:\t")+aws_del["bucket"]["Location"].replace("/", ""))
print(colored(255, 255, 0, " - RDS database: "))
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
        delete_all(iam, s3, aws_del)
