# DataCrossways

Datacrossways is a lightweight, cloud based data management service. The service supports data upload, storage, data sharing, and fine grained data access control. It was designed to be easily deployed on Amazon AWS.

Launcher of data portal using the Flask API and React fronted. Datacrossways is meant for deployment on Amazon AWS. It allows users to connect to a React frontend or access resources programmatically, by directly interacting with the Datacrossways API. The frontend receives all information from the Datacrossways API.

The API accesses a Postgres database that persists information. The API needs access to some AWS resources and requires limited AWS permissions that are passes by a configuration file. Specifically the API requires to create S3 buckets and upload and retrieve files from it.

<img src="https://user-images.githubusercontent.com/32603869/176254810-7a3bc02e-f47d-4c54-a939-9d1aef7d0df9.png" width="400">

---


## Contents

### AWS/cloud configuration
[GoogleOAuth configuration](#googleoauth-configuration) •
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

## Before you start

Decide on a domain (e.g. datacrossways.org) and get a fixed/elastic IP address. These should be the first steps to take. Then follow all other instructions below for an easy setup of a Datacrossways instance. The whole process should not take too long. To register a new domain you can use the AWS `Route53` service. During the setup process, you will need to provide the domain name.

### GoogleOAuth configuration

Datacrossways currently uses Google OAuth to manage user logins. It is a prerequisite for initializing a Datacrossways instance. To set up credentials go to [https://console.cloud.google.com/apis/dashboard](https://console.cloud.google.com/apis/dashboard), where you need to have an account, or you need to create a new one.

If not done so you will have to configure your `OAuth consent screen` first. Fill out the information such as domain and admin email. In the scopes section, select the first three options:

![image](https://github.com/MaayanLab/datacrossways/assets/32603869/0c6d09fb-21c5-43b7-8297-2835acfdd02a)

Then Save and continue. Next, you can add test users. While you are still testing the website, only the test users can use the OAuth login.

![oauth1](https://user-images.githubusercontent.com/32603869/176709575-b5c6b8b2-7873-42c3-bb7d-bd899a2f8368.png)

Click on `+ CREATE CREDENTIALS` and select `OAuth client ID`. There, create a new `web application` entry and fill in the `Authorized JavaScript origins` and `Authorized redirect URIs`. Here we can set multiple domains (choose one you want to use and own) that we would like to use. For the redicrect URL add following entry: `https://<domain>/api/user/authorize?provider=google`.  Then select `CREATE`.

![image](https://github.com/MaayanLab/datacrossways/assets/32603869/b970d1a2-4f9a-4e62-ba26-dc89ec170bf4)

The newly created entry should appear under `OAuth 2.0 Client IDs`. Click `Download OAuth client` and save `Your Client ID` and `Your Client Secret` as a JSON. This file can later be used when deploying the Datacrossways instance, so keep it handy.

### Orcid OAuth

Datacrossways also supports Orcid. Log into Orcid and then under `Profile View` select `Developer Tools`. Here you can configure the required information. The redirect URI should be base_url+`/api/user/authorize?provider=orcid` (Example: https://datacrossways.org/api/user/authorize?provider=orcid). To enable Orcid add the Orcid account information to the `config.json` in the OAuth section, once it is created during the setup process. It should look something like:
```
"oauth":{
    "orcid": {
        "client_id": "APP-B2KWOS2DS3DSJJH",
        "client_secret": "32120d-0981-7453e-lk982-okas908ahjk23"
    },
    "google": { ... }
}
```

## AWS/cloud configuration

Datacrossways requires several AWS resources to be configured before the datacrossways API and frontend can run. While most of the configuration is automated there are some initial steps that need to be performed manually. The first step is to create a `temporary role` with credentials to create the final `user` credentials and `S3 bucket`, as well as an `RDS database`.


### Create a temporary AWS role

This role will only be used to set up the required AWS resources. After the setup, this role can be removed again. Generally, this many user rights can be problematic and you want to limit the instance user rights once the resources are created.

Log into the AWS dashboard at https://aws.amazon.com. 
 - Navigate to create role under IAM
    - navigate to IAM
    - under `Access management` select `Roles` in the left menu
    - Select `Create role` button
 - Create Role
    - select AWS service and use case EC2
    - Select `Next` button
 - Attach Permissions
    - In `filter policies` type `EC2FullAccess` press `enter` and check box
    - In `filter policies` type `IAMFullAccess` press `enter` and check box
    - In `filter policies` type `AmazonS3FullAccess` press `enter` and check box
    - In `filter policies` type `AmazonRDSFullAccess` press `enter` and check box
    - - In `filter policies` type `AWSLambda_FullAccess` press `enter` and check box
    - Select `Next` button
 - Add name and description
    - Choose a unique role name
    - write a description `role for datacrossways configuration`
    - select `Create role` button

When all is done, the user should look something like this:

![role_aws](https://github.com/MaayanLab/datacrossways/assets/32603869/f19a0784-85ed-4898-9112-467279df1acb)


### Create EC2 instance

Depending on the deployment, this instance can be used to host the Datacrossways API and frontend, or can only be used to configure the AWS resources (in case of running the API and frontend locally for development). A small, cost-efficient instance should be sufficient for most use cases (`t2.small`). Data traffic bypasses the host server, so it does not require significant harddisc space. It is recommended to have at least `20GB` to build all docker images when Datacrossways is deployed on this host.

Assuming you want to create resources in region `us-east-1` you can first create an `Elastic IP address`. These IP addresses will remain reserved, even if you should terminate the AWS instance. This is recommended to make sure the domain will be properly linked to your datacrossways instance. Navigate to https://us-east-2.console.aws.amazon.com/ec2/home?region=us-east-1#Addresses: and select `Allocate Elastic IP address`. Then select `Allocate`. Adding a tag is optional.

Log into the AWS dashboard at https://aws.amazon.com. 
 - Navigate to EC2 dashboard
    - Search for service EC2 which should open the EC2 dashboard
    - Select `Launch Instance` button, click `Launch Instance`
 - Configure Instance
    - Under `Quick Start` select `Ubuntu` (as time of writing Ubuntu Server, 22.04 LTS (HMV), SSD Volume Type)
    - Under `Instance` type select desired instance (at least `t2.small` @0.023/h or ~ $17/month), other good options are the other `t2/t3` burstable instances.
          - Pricing overview https://aws.amazon.com/ec2/pricing/on-demand/
    - Under `Key pair` either use an existing `key pair` or generate a new one
          - Enter key pair name and download `.pem` if working on UNIX or `.ppk` when working with Windows and Putty. The `pem/ppk` file is used to log into the instance once created. Under UNIX the key should be placed into a folder with limited user rights (chmod 700) and the key (chmod 600) 
    -  Under `Configure Storage` set to at least `20GB`. Space is mainly needed to build Docker images. If disk space is too small it can result in some minor issues.
    -  After selecting storage space change from `Not encrypted` to `Encrypted`. Then select the `(default) aws/ebs` key under `KMS key` to encrypt the hard drive
    -  Optional but highly recommended: Under `Network settings` restrict SSH traffic to `My IP`
    -  Select `Allow HTTPS traffic from internet`
    -  Select `Allow HTTP traffic from internet`
    -  Under `Advanced details` select IAM instance profile and select the role created before
    -  Select `Launch Instance` button
    -  Assuming `us-east-1` navigate to `https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#Instances:instanceState=running` select newly created instance, select `Actions`, `Networking`, `Manage IP addresses` and attach `Elastic IP`
    -  Select newly created instance in table and copy `Public IPv4 address`
    -  Under UNIX connect to instance with `ssh -i pathtokey/key.pem ubuntu@ipaddress`
    -  Windows users: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html
Under EC2 select the newly created instance. The public IP can be found in the `Instance Details` tab.

![image](https://github.com/MaayanLab/datacrossways/assets/32603869/2e513efb-8039-47d7-a743-fc6b60473556)


### Register a domain

Datacrossways needs to be accessible via a dedicated domain. The easiest way is to register a domain using Route53 which is a service from AWS. First, check if the domain is still available. If it is you can proceed to checkout.

<img width="1241" alt="image" src="https://github.com/MaayanLab/datacrossways/assets/32603869/1c3846fb-3f1c-4b94-a907-8a1213742423">

Then follow the descriptions of the registration to complete the domain registration. The domain will then be accessible after some time (usually a couple of minutes). Once the domain is registered you need to link your AWS instance with the domain. Under `hosted zones` (https://us-east-1.console.aws.amazon.com/route53/v2/hostedzones) select the newly created domain and add a new record.

Select `Create Record` and in the following dialogue paste the IP address of the newly created instance into the `Value` field. All other settings should be left unchanged. Make sure the record type is `A - Routes traffic to an IPv4 address and some AWS resources`. Then create the record.

### Create AWS resources

Now it is time to create the other AWS resources. They encompass a designated user to control S3 access, an S3 bucket with specific configurations, as well as an RDS database to store metadata on stored data objects.

After creating a temporary user and an AWS instance log into the server. From there get `Datacrossways` using git.
```sh
git clone https://github.com/MaayanLab/datacrossways.git
```

Now assuming you have generated and downloaded the OAuth information described in the section above (`GoogleOAuth configuration`) copy the JSON into a folder named `~/datacrossways/secrets`. You can create a new file with the information downloaded from the Google Developer Console. The file can be named any way you like. The code below is an example of how you can create this file:

```sh
mkdir ~/datacrossways/secrets
vi ~/datacrossways/secrets/google_oauth.json
```

Go into the `datacrossways` folder in the home directory and run the command below. It will ask for some required information.
```sh
~/datacrossways/setup.sh
```
Now you can run the aws configuration script which will create the resources. Project names should not contain `commas`, `periods`, `underscores`, or `spaces`. Since the `bucket name` is created from the project name there can be a conflict. The bucket name is `<project_name>-dxw-vault`. Since bucket names are globally unique this might lead to errors. So make sure the project name is unique to avoid conflicts with existing resources.

![image](https://user-images.githubusercontent.com/32603869/181282184-4bc81bb8-4f00-417e-99e6-dc8db43a1b1e.png)


### Remove AWS resources

Warning: When this is run all uploaded data is deleted permanently!

To remove resources created before run the following command and follow onscreen instructions:
```sh
python3 ~/datacrossways/aws/aws_remove.py <project_name>
```
This script relies in a config file `~/datacommons/secrets/aws_config_<project_name>-dxw.json` that is automatically generated when running `aws_setup.py`. The database will take more than a minute to fully shut down completely, the status can be seen in the RDS section of the AWS console. While the status is ![image](https://user-images.githubusercontent.com/32603869/181263946-5e91469d-88f8-49f5-b8c1-085b5e0947f5.png)
 the database name can not be reused. Deleting the security group may fail as it is still linked to the RDS which takes time to delete. You can rerun the script after the RDS is completely shut down or remove the security group manually.

![image](https://user-images.githubusercontent.com/32603869/181263067-4b8a7159-4fe8-4f19-9ee3-6653da20e266.png)

### Remove Manually

In case of an error (e.g. the aws_config_<project_name>-dxw.json) gets lost the resources can easily be removed manually. The resources will be in `RDS`, `IAM`, and `S3`. To delete:

 - Delete user
    - Go to https://us-east-1.console.aws.amazon.com/iamv2/home#/users
    - Find user <project_name>-dxw-user and select checkbox and then `Delete` (if the temporary user is still there also remove this user)
 - Delete policy
    - Go to https://us-east-1.console.aws.amazon.com/iamv2/home#/policies
    - Type `dxw` in the filter input and hit enter
    - Select policy and under `Actions` select delete
 - Delete RDS database
    - Assuming the database was generated in `us-east-1`, go to https://us-east-1.console.aws.amazon.com/rds/home?region=us-east-1#databases
    - Select `<project_name>-dxw-db` and under `Actions` select `Delete`
 - Delete S3 bucket
    - Assuming the database was generated in `us-east-1`, go to https://s3.console.aws.amazon.com/s3/buckets?region=us-east-1
    - Search for `dxw` and select `<project_name>-dxw-vault`
    - First select `Empty` and then `Delete`
 - Security group
    -  Assuming the database was generated in `us-east-1`, go to https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#SecurityGroups
    -  Search for `<project_name>` and select `<project_name>-dxw`
    -  Under actions select `Delete security groups`
    -  The security group can only be deleted once the RDS instance is completely shut down. This process can take more than a minute.

## Local deployment
The `backend API` and `React fronend` can be deployed on a local computer, mainly for development purposes. They still require the AWS resources like the `database` and `S3 bucket` configuration. The setup is described in detail [here](#aws-resource-configuration).


## Cloud deployment

Most of the work is done when the AWS resources were created. The remaining steps are launching the API and frontend using docker-compose.

### Deploy Datacrossways for development

For development, the Oauth authentification might be problematic, especially when the font end is developed on a different server. For this reason there The developer flag has to be added in the config file. This will then bypass any authentification requirements and assume a generic admin user. To modify the behavior edit `~datacrossways/secrets/config.json` and set the field `development` to be either `true` or `false`. By default, the development status is `false`.

#### Start Services

`Before you continue make sure you log out and back in after running setup.sh.` To start the datacrossway service run the command below. It will ask for some additional information. Namely for the domain name and an email required for Let's Encrypt notifications. The domain should be entered in this format without protocol prefix e.g. `datacrossways.org`.
```
~/datacrossways/start.sh
```

#### Stop Services

The following command will stop the docker containers
```
~/datacrossways/stop.sh
```

#### Remove Services
Removing the docker containers will not remove any of the persisted data in the database or the S3 bucket. If you want to permanently delete the project first run 

```
cd ~/datacrossways
docker compose down
```

And then remove all the cloud resources following the steps described [here](#remove-aws-resources).

### Common errors when deploying Datacrossways

There are a lot of steps to deploy Datacrossways and some will cause problems down the road and prevent successful deployment. this section collects common issues that are encountered:

- `AWS instance is not an Ubuntu instance.` Make sure you select the Ubuntu option when launching an instance.
- `OAuth does not work (redirect not valid).` Make sure the URL uses `https`.

## Local deployment

Even though the API and React frontend are running locally, the cloud resources are still required. To create them please go through the steps described [here](#googleoauth-configuration) first. When the `S3 bucket` is created with all additional configuration proceed to deploy the API.

### Deploy API locally

First get the API code using git:
```sh
git clone https://github.com/MaayanLab/datacrossways_api
```
Then navigate to the `datacorssways_api` folder. The API requires a config file `secrets/config.json`. The configuration contains information about:

 - Internal URLs (`api`, `fronend`, `redirect`)
 - GoogleOAuth client credentials
 - Database credentials
 - AWS user credentials (Important: these are the credentials from the AWS user that has only read and write access to the newly created S3 bucket and NOT the `temporary user`)

The `config.json` file can be created after setting up all AWS resource. For this run `python3 ~/datacrossways/aws/aws_setup.py <aws_id> <aws_key> <project_name>` and follow the instructions to retrieve the `Google OAuth credentials` [here](#googleoauth-configuration). The `JSON` file from the `Google Developer Console` should be copied into `~/datacrossways/secrets/` (the name of the file is not important, it will be automatically detected).

```sh
python ~/datacrossways/create_config.py <project_name>
```
This will generate a file at `~/datacrossways/secrets/config.json`.

Then run:

```sh
mkdir ~/datacrossways_api/secrets
mv ~/datacrossways/secrets/conf.json~/datacrossways_api/secrets/config.json

cd ~/datacrossways_api
flask run
```

The API should now be up and running

#### secrets/config.json
```json
{
    "api":{
        "url": "http://localhost:5000"
    },
    "frontend": {
        "url": "http://localhost:3000/"
    },
    "redirect": "http://localhost:5000/",
    "oauth": {
        "google": {
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "client_id": "XXXXXXXXXXXXX-xxxxxxxxxxxxxxxx.apps.googleusercontent.com",
            "client_secret": "XXXXXXXXXX-xxxxxxxxxxxxx",
            "javascript_origins": [
                "http://localhost:5000"
            ],
            "project_id": "xxxxxxxxxx",
            "redirect_uris": [
                "http://localhost:5000/authorize"
            ],
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    "aws": {
        "aws_id": "xxxxxxxxxxxxxxxx",
        "aws_key": "xxxxxxxxxxxxxx",
        "bucket_name": "unique_bucket_name",
        "region": "us-east-1"
    },
    "database":{
        "user": "xxxxxxx",
        "pass": "xxxxxxxxxxxxx",
        "server": "xxxxxxxxxx.xxxxx.rds.amazonaws.com",
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

