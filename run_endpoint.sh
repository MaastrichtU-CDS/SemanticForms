docker run -d \
    --name graphdb \
    -p 7200:7200 \
    --restart unless-stopped \
    registry.gitlab.com/um-cds/fair/tools/docker-graphdb:latest
