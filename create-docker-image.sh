docker build -t winklermw-mz/bugblitz .
docker run -d --name BugBlitz --network my-local-net -v /Users/markus/storage/bugblitz:/app/instance -p 8003:8003 winklermw-mz/bugblitz