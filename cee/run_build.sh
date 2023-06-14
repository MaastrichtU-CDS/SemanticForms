NODE_VERSION=16

docker volume create node-$NODE_VERSION-cedar-build

rm -Rf $(pwd)/output

docker run --rm -v $(pwd)/input:/input -v $(pwd)/output:/output -v node-$NODE_VERSION-cedar-build:/build node:$NODE_VERSION-bullseye /bin/bash /input/build_frontend.sh

mkdir -p $(pwd)/../src/static/cee/node_modules
cp $(pwd)/output/cedar-embeddable-editor.js > $(pwd)/../src/static/cee/cedar-embeddable-editor.js

docker run --rm -v $(pwd)/output:/output --workdir /output node:$NODE_VERSION-bullseye npm install @webcomponents/webcomponentsjs

cp -R $(pwd)/output/node_modules $(pwd)/../src/static/cee
cp $(pwd)/output/styles.css $(pwd)/../src/static/cee/
cp $(pwd)/output/MaterialIcons-* $(pwd)/../src/static/cee/