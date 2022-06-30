

# this was tested on an t2.small instance running Ubuntu 22.04 LTS (GNU/Linux 5.15.0-1011-aws x86_64)
# 8 GB disk space / I would recommend slightly more (can run out of space when building the docker images)

# add secrets folder to datacrossways folder, and add config.json
sudo apt-get update

python3 -m pip install psycopg2-binary

if ! command -v docker ps /dev/null
then
    sudo apt install docker.io -y

    sudo groupadd docker
    sudo usermod -aG docker $USER
    newgrp docker

    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
fi

sudo apt-get install python3-pip -y
pip3 install -r requirements.txt
