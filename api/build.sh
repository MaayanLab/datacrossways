# get rid of old stuff
docker rmi -f $(docker images | grep "^<none>" | awk "{print $3}")
docker rm $(docker ps -q -f status=exited)

docker kill datacrosswayapi
docker rm datacrosswayapi

../stop.sh

y | docker image prune -a

docker build --no-cache=true -f Dockerfile -t datacrossways_api .

#docker build --no-cache=true -f Dockerfile -t maayanlab/datacrosswayapi:0.0.1 .
#docker build --no-cache=true -f DockerfileUnicorn -t maayanlab/datacrosswayapiunicorn:0.0.1 .

#docker push maayanlab/datacrosswayapi:0.0.1

