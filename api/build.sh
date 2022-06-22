# get rid of old stuff
docker rmi -f $(docker images | grep "^<none>" | awk "{print $3}")
docker rm $(docker ps -q -f status=exited)

docker kill datacrosswayapi
docker rm datacrosswayapi

docker build -f DockerfileCamel -t maayanlab/datacrosswayapi .

docker push maayanlab/datacrosswayapi:0.0.1

