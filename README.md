# DataCrossways

Launcher of data portal using the flask API and React fronted. Datacrossways is meant for deployment on Amazon AWS. I allows users to connect to a React frontend or access resources programmatically, by difectly interacting with the Datacrossways API. The frontend receives all information from the Datacrossways API.

The API accesses a Postgres database that persists information. The API needs access to some AWS resources and requires limited AWS permissions that are passes by a configuration file. Specifically the API requires to create S3 buckets and upload and retrieve files from it. 

<img src="https://user-images.githubusercontent.com/32603869/176254810-7a3bc02e-f47d-4c54-a939-9d1aef7d0df9.png" width="400">

## AWS resource configureation

Datacrossways requires several AWS resources to be configured before the datacrossways API and frontend can run. While most of the configuration is automated there are some initial steps that need to be performed manually. The first step is to create a `temporary user` with credentials to create the final `user` credentials and `S3 bucket`, as well as a `RDS database`.

### Create temporary user

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
    -> Select `Attach existing policies directly`
    -> In `filter policies` type `IAMFullAccess` and check box
    -> In `filter policies` type `AmazonS3FullAccess` and check box
    -> Select `Next: Tags` button
 - Add Tag
    - Select `Next: Review`
 - Review
    - Select `Create User`
 - Save `Access key ID` and `Secret access key` and keep them save

## Launch locally
The backend and fronend can be deployed independently for development purposes. 

### Run API

First get the API code usig git:
```
git clone https://github.com/MaayanLab/datacrossways_api
```
Then navigate to the `datacorssways_api` folder. The API requires a config file `secrets/conf.json`. The format of the file should contain information about the database, OAuth credentials, and AWS credentials.

#### secrets/conf.json
```
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

## Run frontend locally

The React frontend depends on the API, so it should be set up first. Then get the frontend using git with:

```
git clone https://github.com/MaayanLab/datacrossways_frontend
```
Navigate into the project folder and run `npm install --legacy-peer-deps`. To start the frontend run `npm run dev`. The fronend is currently accessed via the API port at `http://localhost:5000`.

