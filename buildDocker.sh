docker kill $(docker ps -qa)
docker rm -v $(docker ps -qa)
docker rmi -f $(docker images -q)

docker compose build --no-cache
