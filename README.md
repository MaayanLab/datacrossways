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

## AWS/cloud configuration

Datacrossways requires several AWS resources to be configured before the datacrossways API and frontend can run. While most of the configuration is automated there are some initial steps that need to be performed manually. The first step is to create a `temporary user` with credentials to create the final `user` credentials and `S3 bucket`, as well as a `RDS database`.

### GoogleOAuth configuration

Datacrossways currently uses google OAuth to manage user logins. To set up credentials go to [https://console.cloud.google.com/apis/dashboard](https://console.cloud.google.com/apis/dashboard), where you need to have an account or you need to create a new one.

![oauth1](https://user-images.githubusercontent.com/32603869/176709575-b5c6b8b2-7873-42c3-bb7d-bd899a2f8368.png)

Click on `+ CREATE CREDENTIALS` and select `OAuth client ID`. There create a new `web application` entry and fill in the `Authorized JavaScript origins` and `Authorized redirect URIs`. Here we can set multiple domains (choose one you want to use and own) that we would like to use. The `localhost` entries allow us to run Datacrossways locally. The click `CREATE`.

<img width="425" alt="oauth2" src="https://user-images.githubusercontent.com/32603869/176705928-fd5adccc-31a4-4b04-8a3f-66085d888677.png">

The newly created entry should now appear under `OAuth 2.0 Client IDs`. Click `Download OAuth client` and save `Your Client ID` and `Your Client Secret`.

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

Depending on the deployment this instance can be used to host the Datacrossways API and frontend, or can only be used to configure the AWS resources (in case of running the API and frontend locally for development). A small, cost efficient instance should be sufficient for most use cases (`t2.small`). Data traffic bypasses the host server, so it does not require significant harddisc space. It is recommended to have at least `20GB` to build all docker images when Datacrossways is deployed on this host.

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
    -  Under `Configure Storage` set to at least `20GB`. Space is mainly needed to build Docker images. If disk space is too small it can result in some minor issues.
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
Now you can run the aws configuration script which will create the resources. To run it requires the temp user credentials and a project name. Project names should not contain `commas`, `periods`, `underscores`, or `spaces`. Since the `bucket name` is created from the project name there can be a conflict. The bucket name is `<project_name>-dxw-vault`. Since bucket names are globally unique this might lead to errors. Run the following command:

```sh
python3 ~/datacrossways/aws/aws_setup.py <aws_id> <aws_key> <project_name>
```

![image](https://user-images.githubusercontent.com/32603869/181282184-4bc81bb8-4f00-417e-99e6-dc8db43a1b1e.png)


### Remove AWS resources

Warning: When this is run all uploaded data is deleted permanently!

To remove resources created before run the following command and follow onscreen instructions:
```sh
python3 ~/datacrossways/aws/aws_remove.py <aws_id> <aws_key> <project_name>
```
This script relies in a config file `~/datacommons/secrets/aws_config_<project_name>-dxw.json` that is automatically generated when running `aws_setup.py`. The database will take more than a minute to fully shut down completely, the status can be seen in the RDS section of the AWS console. While the status is ![image](https://user-images.githubusercontent.com/32603869/181263946-5e91469d-88f8-49f5-b8c1-085b5e0947f5.png)
 the database name can not be reused.

![image](https://user-images.githubusercontent.com/32603869/181263067-4b8a7159-4fe8-4f19-9ee3-6653da20e266.png)

### Remove manually

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

## Local deployment
The `backend API` and `React fronend` can be deployed on a local computer, mainly for development purposes. They still require the AWS resources like the `database` and `S3 bucket` configuration. The setup is described in details [here](#aws-resource-configuration).



## Cloud deployment

### Deploy Datacrossways for development

For development the Authentification might be problematic, especially when the font end is developed on a different server. For this reason there is a separate way to deploy the API. The developer flag has to be added in the config file. This will then bypass any authentification requirements and assume a generic admin user.

```
docker compose up
```

### Deploy Datacrossways for production



<img width="140" alt="under construction" src="https://user-images.githubusercontent.com/32603869/176712238-a90f801e-6f65-42fc-851f-31a5cff3c6cd.png">

This section is currently being worked on.

---

## Local deployment

Even though the API and React frontend are running locally, the cloud resources are still required. To create them please go through the steps described [here](#googleoauth-configuration) first. When the `S3 bucket` is created with all additional configuration proceed to deploy the API.

### Deploy API locally

First get the API code usig git:
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
    "db":{
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

