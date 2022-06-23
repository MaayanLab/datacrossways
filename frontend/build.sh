# get rid of old stuff
docker rmi -f $(docker images | grep "^<none>" | awk "{print $3}")
docker rm $(docker ps -q -f status=exited)

docker kill datacrosswayui
docker rm datacrosswayui

docker build --no-cache=true -f Dockerfile -t maayanlab/datacrosswayui:0.0.1 .

docker push maayanlab/datacrosswayui:0.0.1

