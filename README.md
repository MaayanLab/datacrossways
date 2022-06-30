# DataCrossways

Launcher of data portal using the flask API and React fronted. Datacrossways is meant for deployment on Amazon AWS. I allows users to connect to a React frontend or access resources programmatically, by difectly interacting with the Datacrossways API. The frontend receives all information from the Datacrossways API.

The API accesses a Postgres database that persists information. The API needs access to some AWS resources and requires limited AWS permissions that are passes by a configuration file. Specifically the API requires to create S3 buckets and upload and retrieve files from it. 

<img src="https://user-images.githubusercontent.com/32603869/176254810-7a3bc02e-f47d-4c54-a939-9d1aef7d0df9.png" width="400">

---

## Contents

### AWS configuration
[Create temporary AWS user](#create-temporary-aws-user) •
[Create EC2 instance](#create-ec2-instance) •
[Create AWS resources](#create-aws-resources) •
[Remove AWS resources](#remove-aws-resources)

### Cloud deployment
[Deploy Datacrossways for production](#deploy-datacrossways-for-production)

### Local deployment
[Deploy API locally](#deploy-api-locally) •
[Deploy React frontend locally](#deploy-api-locally)

---

## AWS resource configuration

Datacrossways requires several AWS resources to be configured before the datacrossways API and frontend can run. While most of the configuration is automated there are some initial steps that need to be performed manually. The first step is to create a `temporary user` with credentials to create the final `user` credentials and `S3 bucket`, as well as a `RDS database`.


### Create temporary AWS user

This user will only be used to set up the required AWS resources. After the setup this user should be removed again.

Log into the AWS dashboard at https://aws.amazon.com. 
 - Navigate to create user under IAM
    - navigate to IAM
    - under `Access management` select `Users` in the left menu
    - Select `Add users` button
 - Create User
    - choose a unique username e.g. `datacrossways_config_temp`
    - check box `Access key - Programmatic access`
    - Select `Next: Permissions` button
 - Attach Permissions
    - Select `Attach existing policies directly`
    - In `filter policies` type `IAMFullAccess` and check box
    - In `filter policies` type `AmazonS3FullAccess` and check box
    - In `filter policies` type `AmazonRDSFullAccess` and check box
    - Select `Next: Tags` button
 - Add Tag
    - Select `Next: Review`
 - Review
    - Select `Create User`
 - Save `Access key ID` and `Secret access key` and keep them safe

When all is done the user should look something like this:
<img width="1060" alt="Temporary User" src="https://user-images.githubusercontent.com/32603869/176680884-a375eaca-88bb-4e8e-8884-2b5ad2675db4.png">


### Create EC2 instance

Depending on the deployment this instance can be used to host the Datacrossways API and frontend, or can only be used to configure the AWS resources (in case of running the API and frontend locally for development). A small, cost efficient instance should be sufficient for most use cases (`t2.small`). Data traffic bypasses the host server, so it does not require significant harddisc space. It is recommended to have at least `10GB` to build all docker images when Datacrossways is deployed on this host.

Log into the AWS dashboard at https://aws.amazon.com. 
 - Navigate to EC2 dashboard
    - Search for service EC2 which should open the EC2 dashboard
    - Select `Launch Instance` button, click `Launch Instance`
 - Configure Instance
    - Under `Quick Start` select `Ubuntu` (as time of writing Ubuntu Server, 22.04 LTS (HMV), SSD Volume Type)
    - Under `Instance` type select desired instance (at least `t2.small` @0.023/h or ~ $17/month), other good options are the other `t2` burstable instances.
          - Pricing overview https://aws.amazon.com/ec2/pricing/on-demand/
    - Under `Key pair` either use an existing `key pair` or generate a new one
          - Enter key pair name and download `.pem` if working on UNIX or `.ppk` when working with Windows and Putty. The `pem/ppk` file are used to log into the instance once it is created. Under UNIX the key should be placed into folder with limited user rights (chmod 700) and the key (chmod 600) 
    -  Under `Configure Storage` set to at least `10GB`. Space is mainly needed to build Docker images. If disk space is too small it can result in some minor issues.
    -  Optional: Under `Network settings` restrict SSH traffic to `My IP`
    -  Select `Launch Instance` button
    -  Select newly created instance in table and copy `Public IPv4 address`
    -  Under UNIX connect to instance with `ssh -i pathtokey/key.pem ubuntu@ipaddress`
    -  Windows users: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html


### Create AWS resources

Now it is time to create the AWS resources. They encompass a designated user to control S3 access, a S3 bucket with specific configurations, as well as a RDS database to store metadata on stored data objects.

After creating a temporary user and an AWS instance log into the server. From there get `Datacrossways` using git.
```sh
git clone https://github.com/MaayanLab/datacrossways.git
```
Go into the `datacrossways` folder in the home directory and run the command below to install some dependencies.
```sh
~/datacrossways/setup.sh
```
Now you can run the aws configuration script which will create the resources. To run it requires the temp user credentials and a project name. Project names should not contain `commas`, `periods`, `underscores`, or `spaces`. Since the `bucket name` is created from the project name there can be a conflict. The bucket name is `<project_name>-vault`. Since bucket names are globally unique this might lead to errors. Run the following command:

```sh
python3 ~/datacrossways/aws/aws_setup.py <aws_id> <aws_key> <project_name>
```


### Remove AWS resources

Warning: When this is run all uploaded data is deleted permanently!

To remove resources created before run the following command and follow onscreen instructions:
```sh
python3 ~/datacrossways/aws/aws_remove.py <aws_id> <aws_key> <project_name>
```
This script relies in a config file `~/datacommons/aws/aws_config_<project_name>-dxw.json` that is automatically generated when running `aws_setup.py`.

## Local deployment
The `backend API` and `React fronend` can be deployed on a local computer, mainly for development purposes. They still require the AWS resources like the `database` and `S3 bucket` configuration. The setup is described in details [here](#aws-resource-configuration).

---

## Local deployment

### Deploy API locally

First get the API code usig git:
```sh
git clone https://github.com/MaayanLab/datacrossways_api
```
Then navigate to the `datacorssways_api` folder. The API requires a config file `secrets/conf.json`. The format of the file should contain information about the database, OAuth credentials, and AWS credentials.


#### secrets/conf.json
```json
{
    "api":{
        "url": "http://localhost:5000"
    },
    "frontend": {
        "url": "http://localhost:3000/"
    },
    "redirect": "http://localhost:5000/",
    "web": {
        "client_id": "xxxxxxxxxxxxxxx.apps.googleusercontent.com",
        "project_id": "xxxxxxxxxxxxx",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "xxxxxxxxxxxxxxxxxxxxxxx",
        "redirect_uris": [
            "http://localhost:5000/login",
            "http://localhost:5000/authorize",
            "http://127.0.0.1:5000/authorize"
        ],
        "javascript_origins": [
            "http://localhost:5000"
        ]
    },
    "aws": {
        "aws_id": "xxxxxxxxxxxxxxxx",
        "aws_key": "xxxxxxxxxxxxxx",
        "bucket_name": "unique_bucket_name",
        "region": "us-east-1"
    },
    "db":{
        "user": "xxxxxxx",
        "pass": "xxxxxxxxxxxxx",
        "server": "xxxxxxxxxx.us-east-1.rds.amazonaws.com",
        "port": "5432",
        "name": "xxxxxxxxx"
    }
}
```

The API is a flask application and can be started using the command `flask run`.


## Deploy React frontend locally

The React frontend depends on the API, so it should be set up first. Then get the frontend using git with:

```
git clone https://github.com/MaayanLab/datacrossways_frontend
```
Navigate into the project folder and run `npm install --legacy-peer-deps`. To start the frontend run `npm run dev`. The fronend is currently accessed via the API port at `http://localhost:5000`.

