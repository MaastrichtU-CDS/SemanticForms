docker-compose up -d

echo "Waiting for GraphDB to be up-and-running"
curl -X GET --header 'Accept: application/json' 'http://localhost:7200/rest/locations'
retVal=$?
while [ $retVal -ne 0 ]
do
    sleep 5
    curl -X GET --header 'Accept: application/json' 'http://localhost:7200/rest/locations'
    retVal=$?
done

# Create repository from config
curl -X POST -F config=@config.ttl --header 'Content-Type: multipart/form-data' --header 'Accept: */*' 'http://localhost:7200/rest/repositories'