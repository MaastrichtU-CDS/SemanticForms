NODE_VERSION=14
rm -Rf $(pwd)/output

docker run --rm -it -v $(pwd)/input:/input -v $(pwd)/output:/output node:$NODE_VERSION-bullseye /bin/bash /input/build_frontend.sh

cat output/{runtime,polyfills,main}.js > "../src/static/cee/cedar-embeddable-editor.js"

docker run --rm -it -v $(pwd)/output:/output --workdir /output node:$NODE_VERSION-bullseye npm install @webcomponents/webcomponentsjs

cp -R output/node_modules ../src/static/cee/node_modules
cp output/{MaterialIcons-*,styles.css} ../src/static/cee/
