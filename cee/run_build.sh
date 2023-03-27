docker run --rm -it -v $(pwd)/input:/input -v $(pwd)/output:/output node:14-bullseye /bin/bash /input/build_frontend.sh

cat output/{runtime,polyfills,main}.js > "../../src/static/cee/cedar-embeddable-editor.js"