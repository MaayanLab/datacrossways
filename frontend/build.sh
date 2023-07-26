docker rmi -f $(docker images | grep "^<none>" | awk "{print $3}")
docker rm $(docker ps -q -f status=exited)

docker kill datacrosswayfrontend
docker rm datacrosswayfrontend

../stop.sh

docker rmi datacrossways_frontend
#docker image prune -a -f

docker build --no-cache=true -f Dockerfile -t datacrossways_frontend .