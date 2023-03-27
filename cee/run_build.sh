rm -Rf $(pwd)/output

docker run --rm -it -v $(pwd)/input:/input -v $(pwd)/output:/output node:14-bullseye /bin/bash /input/build_frontend.sh

docker run --rm -it -v $(pwd)/output:/output --workdir /output node:14-bullseye npm install @webcomponents/webcomponentsjs

cat output/{runtime,polyfills,main}.js > "../src/static/cee/cedar-embeddable-editor.js"
cp -R output/node_modules ../src/static/cee/node_modules
cp output/{MaterialIcons-*,styles.css} ../src/static/cee/
