docker build -t winklermw-mz/bugbench .
docker run -d --name BugBench --network my-local-net -v /Users/markus/storage/bugbench:/app/instance -p 8100:8100 winklermw-mz/bugbench