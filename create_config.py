import json
import sys
import os
from os import listdir
import traceback

PROJECT_NAME = sys.argv[1]
DOMAIN = sys.argv[2]
path = os.path.dirname(__file__)

aws_creds = {}
try:
    with open(path+"/secrets/aws_config_"+PROJECT_NAME+"-dxw.json", "r") as f:
        aws_creds = json.load(f)
except Exception:
    print("Could not read secrets/aws_"+PROJECT_NAME+"-dxw.json file. This file is generated when running aws/aws_setup.py.")
    quit()

google_oauth = {}
for file in listdir(path+"/secrets"):
    try:
        with open(path+"/secrets/"+file) as f:
            google_creds = json.load(f)
            if google_creds["web"]["auth_uri"] == "https://accounts.google.com/o/oauth2/auth":
                google_oauth["web"] = google_creds["web"]
                break
    except Exception:
        x=1

conf = {}
try:
    conf["oauth"] = {}
    if "web" in google_oauth:
        conf["oauth"]["google"] = google_oauth["web"]
    conf["aws"] = {}
    conf["aws"]["aws_id"] = aws_creds["user"]["key"]["AccessKeyId"]
    conf["aws"]["aws_key"] = aws_creds["user"]["key"]["SecretAccessKey"]
    conf["aws"]["bucket"] = aws_creds["bucket"]["Name"]
    conf["aws"]["region"] = aws_creds["bucket"]["Region"]
    conf["database"] = {}
    conf["database"]["user"] = aws_creds["database"]["MasterUsername"]
    conf["database"]["pass"] = aws_creds["database"]["MasterUserPassword"]
    conf["database"]["server"] = aws_creds["database"]["Endpoint"]["Address"]
    conf["database"]["port"] = "5432"
    conf["database"]["name"] = "datacrossways"
    conf["api"] = {"url": "http://api:5000/"}
    conf["frontend"] = {"url": "http://frontend:3000/"}
    conf["redirect"] = {"url": "https://"+DOMAIN}
    conf["development"] = False
except Exception:
    print("Failed to build conf.json")
    traceback.print_exc()
    quit()

with open(path+"/secrets/config.json", "w") as f:
    f.write(json.dumps(conf, indent=4, sort_keys=True, default=str))
