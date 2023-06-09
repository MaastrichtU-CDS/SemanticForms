NODE_VERSION=16

docker volume create node-$NODE_VERSION-cedar-build

rm -Rf $(pwd)/output

docker run --rm -v $(pwd)/input:/input -v $(pwd)/output:/output -v node-$NODE_VERSION-cedar-build:/build node:$NODE_VERSION-bullseye /bin/bash /input/build_frontend.sh

cat output/{runtime,polyfills,main}.js > "../src/static/cee/cedar-embeddable-editor.js"

docker run --rm -v $(pwd)/output:/output --workdir /output node:$NODE_VERSION-bullseye npm install @webcomponents/webcomponentsjs

cp -R output/node_modules ../src/static/cee/node_modules
cp output/{MaterialIcons-*,styles.css} ../src/static/cee/
