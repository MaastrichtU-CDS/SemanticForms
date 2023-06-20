# SemanticForms
A Cedar template implementation to fill in (and maintain) forms, based on the [Cedar Embeddable Editor](https://github.com/metadatacenter/cedar-embeddable-editor)

## Prerequisites
* Docker Engine (linux) / Docker for Windows / Docker for macOS

Additional prerequisites are needed for development:

* Python >= 3.8
* NodeJS v16 and NPM

## How to run
1. Clone or download this GitHub repository to your local PC
2. Open the downloaded/cloned contents locally in the terminal
3. Run `docker-compose up -d`
4. when the previous command is finished, open the following url: [http://localhost:5000](http://localhost:5000)

## Configure templates
By default a CEDAR template is given in [src/template.json](src/template.json). You can change this in the [src/config.yaml](src/config.yaml) file in:
```
template:
    source: cedar
    templateId: <location_of_cedar_json_ld_file>
```

If you want to connect to the CEDAR service API, it is possible to provide the following information in the [src/config.yaml](src/config.yaml) file:
```
template:
    source: cedar
    api_key: <your_api_key>
    templateId: <your_cedar_template_uuid>
```