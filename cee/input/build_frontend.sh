version='2.6.24'

mkdir /build
cd /build

cp /input/*.ts ./

rm -Rf cedar-embeddable-editor*
rm -Rf release-*.zip

# Download and unzip release version of CEE
curl -L -o release-$version.zip https://github.com/metadatacenter/cedar-embeddable-editor/archive/refs/tags/release-$version.zip
unzip release-$version.zip

# # Override files needed to work in our situation
# cp app.component.ts cedar-embeddable-editor-release-$version/src/app/app.component.ts
# cp app.module.ts cedar-embeddable-editor-release-$version/src/app/app.module.ts

# Build project
cd cedar-embeddable-editor-release-$version
sed -i "/this.messageHandlerService.traceObject/ a window.location.href = '\\/';" src/app/modules/shared/components/cedar-data-saver/cedar-data-saver.component.ts
npm install --no-audit
# node_modules/@angular/cli/bin/ng build --configuration production --baseHref="./static/cee/"
export PATH=$(pwd)/node_modules/@angular/cli/bin/:$PATH
ng build --configuration production --output-hashing=none --baseHref="./static/cee/"

# copy output
cp -R ./dist/cedar-embeddable-editor/* /output
