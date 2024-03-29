

# this was tested on an t2.small instance running Ubuntu 22.04 LTS (GNU/Linux 5.15.0-1011-aws x86_64)
# 8 GB disk space / I would recommend slightly more (can run out of space when building the docker images)

if [ $# -eq 0 ] ; then
    printf "To set up a new Datacrossways instance please enter some additional information. Datacrossways will set up all required AWS resources and configure an initial Admin account.\n"
    
    printf "\nPlease enter the information for the initial Admin (currently only Google login is supported via OAuth).\n"
    read -p 'E-mail (@gmail.com): ' EMAIL
    if [[ $EMAIL != *"gmail"* ]]; then
        printf "The e-mail has to be from a gmail account e.g. accountname@gmail.com\n"
        exit 0
    fi
    
    read -p 'First name: ' FIRST_NAME
    read -p 'Last name: ' LAST_NAME

    printf "\nWhat is the domain name you plan to expose the Datacrossways instance (e.g. datacrossways.org)?\n"
    read -p 'Domain: ' DOMAIN

    printf "\nWhat is the project name (e.g. mydatacrossways)? The project name is used to create AWS resource names such as the S3 bucket and the database. The project name has to be unique to avoid conflicts such as already existing S3 bucket names.\n"
    read -p 'Project name: ' PROJECT_NAME

    printf "\nTo set up AWS resources Datacrossways setup requires AWS region. (us-east-1, us-west-1, ...)\n"
    read -p 'AWS region: ' AWS_REGION

    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -

    printf "Admin Information\n"
    printf "E-mail: $EMAIL \n"
    printf "First name:  $FIRST_NAME \n"
    printf "Last name:  $LAST_NAME \n\n"

    printf "Project Information\n"
    printf "Project name:  $PROJECT_NAME \n"
    printf "DOMAIN:  $DOMAIN \n\n"

    printf "AWS Region\n"
    printf "AWS region:  $AWS_REGION \n"

    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -

    read -p 'Please add the OAuth credentials in the folder ~/datacrossways/secrets (https://github.com/MaayanLab/datacrossways#googleoauth-configuration). Is the entered information correct and the are the OAuth credentials present? (Y/n): ' INPUT_OK

    if [[ $INPUT_OK != "Y" ]]; then
        exit 0
    fi
else
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--awsregion)
            AWS_REGION="$2"
            shift # past argument
            shift # past value
            ;;
            -p|--project)
            PROJECT_NAME="$2"
            shift # past argument
            ;;
            -f|--firstname)
            FIRST_NAME="$2"
            shift # past argument
            ;;
            -l|--lastname)
            LAST_NAME="$2"
            shift # past argument
            ;;
            -e|--email)
            EMAIL="$2"
            shift # past argument
            ;;
            -d|--domain)
            DOMAIN="$2"
            shift # past argument
            ;;
            -*|--*)
            echo "Unknown option $1"
            exit 1
            ;;
            *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
            ;;
        esac
    done
fi

if !( [[ -v AWS_REGION ]] && [[ -v DOMAIN ]] && [[ -v FIRST_NAME ]] && [[ -v LAST_NAME ]] && [[ -v EMAIL ]] && [[ -v PROJECT_NAME ]]); then
    printf "Error. Some arguments are missing. Please enter all required arguments"
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
    printf "-p|--project     Project name"
    printf "-d|--domain      Domain (datacrossways.org)"
    printf "-r|--awsregion       AWS region (e.g. us-east-1, us-west-1, ...)"
    printf "-e|--email       Admin email matching Google or Orcid account (e.g. user@gmail.com)"
    printf "-f|--firstname   Admin firstname"
    printf "-l|--lastname    Admin lastname"
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
    exit 0
fi

printf "\nStarting setup....\n\n"

# add secrets folder to datacrossways folder, and add config.json
OLD_DIR=$(pwd)
SCRIPT_DIR=$( dirname -- "$0"; )
cd $SCRIPT_DIR

sudo apt-get update

# Check if docker is installed
if ! command -v docker > /dev/null 2>&1; then
    sudo apt install docker.io -y

    if ! grep -q docker /etc/group; then
        sudo groupadd docker
    fi
    sudo usermod -aG docker $USER
    #newgrp docker
fi

# Check if docker-compose is installed
if [ ! -f ~/.docker/cli-plugins/docker-compose ]; then
    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
fi

sudo apt-get install python3-pip -y
pip3 install -r requirements.txt

python3 aws/aws_setup.py $PROJECT_NAME $AWS_REGION
python3 create_config.py $PROJECT_NAME $DOMAIN

rm -rf datacrossways_api
git clone https://github.com/MaayanLab/datacrossways_api.git

cd datacrossways_api
pip install -r requirements.txt

mkdir -p secrets
cp ../secrets/config.json secrets/config.json
python3 createdb.py $EMAIL $FIRST_NAME $LAST_NAME

cd ..
rm -rf datacrossways_api

cd $OLD_DIR

echo Setup complete! Add additional information to the secrets folder complete configuration and run the create_config.py script. 
echo Please log out and back in to update user rights
echo then run \'~/datacrossways/start.sh\' to deploy Datacrossways