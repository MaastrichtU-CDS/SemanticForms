# SemanticForms
A Cedar template implementation to fill in (and maintain) forms, based on the [Cedar Embeddable Editor](https://github.com/metadatacenter/cedar-embeddable-editor)

## Prerequisites
* linux / unix OS
* Docker Engine
* NodeJS and NPM

## How to run
1. Go to the cee folder, and execute the [build_frontend.sh](cee/build_frontend.sh) file (command: `cd cee && sh build_frontend.sh`)
2. Start the GraphDB backend:
  a. Go to the [development_environment](development_environment) folder
  b. Run `docker-compose up -d`
  c. Run `sh run.sh`
3. Run the python backend (which serves the front-end)
  a. Go to the main folder
  b. Create and load dependencies: `python -m venv ./venv && source ./venv/bin/activate && pip install -r requirements.txt
  c. Go to the [src](src) folder and run `python run.py`

## Configure templates
By default a template is given in [src/template.json](src/template.json). You can change this in the [src/config.yaml](src/config.yaml) file in template -> location.

If you want to connect to Cedar itself, it is possible to provide the following information in the [src/config.yaml](src/config.yaml) file:
```
template:
    source: cedar
    api_key: <your_api_key>
    templateId: <your_cedar_template_uuid>
```
