from operator import truediv
from flask import Flask, Response, request, render_template, redirect
from flask_cors import CORS
import yaml
import os
import requests
import uuid
import json
from rdflib import Graph
import logging
import sys
import datetime
from tzlocal import get_localzone
from persistance import FilePersistance

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
# get local timezone    
local_tz = get_localzone() 

def loadConfig(pathString):
    """
    Load configuration file if found on path
    """
    if os.path.exists(pathString):
        with open(pathString) as f:
            config = yaml.safe_load(f)
            return config
    return { }

config = loadConfig("config.yaml")
if len(config)==0:
    config = loadConfig("../config.yaml")
if len(config)==0:
    logging.error("Could not find config.yaml file. System will exit")
    sys.exit(-1)

persistance = FilePersistance(folder_location=config['server']['storageFolder'],
                              title_uri=config['template']['title_predicate'],
                              base_url=config['template']['instance_base_url'] + "/instance")

@app.route("/")
def index():
    instances = persistance.get_instances()
    
    if config["template"]["storage"]=="cedar":
        return render_template("index.html", instances=instances, template_id=config["template"]["templateId"])
    else:
        return render_template("index.html", instances=instances)

@app.route("/add")
def cee():
    return render_template("cee.html")

@app.route("/instance/<identifier>/edit")
def edit_cee(identifier: str):
    
    if identifier:
        fileNameJson = persistance.get_instance(identifier)['filename']
        with open(fileNameJson, "r") as f:
            jsonData = json.load(f)

            infoData = {}
            
            infoData["isBasedOn"] = jsonData["schema:isBasedOn"]
            infoData["id"] = jsonData["@id"]
            infoData["createdOn"] = jsonData["pav:createdOn"]
            infoData["fileName"] = fileNameJson

            del jsonData["@id"]
            del jsonData["pav:createdOn"]
            del jsonData["schema:isBasedOn"]
        return render_template("cee.html", formData=json.dumps(jsonData), formInfo=json.dumps(infoData))
    
    return redirect("/", error="Could not load data")  

@app.route("/delete")
def delete_instance():
    identifier = request.args.get("uri")
    persistance.delete_instance(identifier)
    return redirect("/")

@app.route("/instance/<identifier>")
def showInstance(identifier: str):
    filename = persistance.get_instance(identifier)['filename']
    with open(filename, "r") as f:
        jsonData = json.load(f)
    
    # if accept method is text/plain return n-triples
    if "application/n-triples" in request.accept_mimetypes.best:
        # Convert jsonData to n-triples
        g = Graph()
        g.parse(data=json.dumps(jsonData), format='json-ld')
        ntriples = g.serialize(format='nt')
        return Response(ntriples, mimetype='application/n-triples')
    
    if "application/json" in request.accept_mimetypes.best:
        return Response(json.dumps(jsonData), mimetype='application/json')
    
    if "application/ld+json" in request.accept_mimetypes.best:
        return Response(json.dumps(jsonData), mimetype='application/ld+json')
    
    if "application/rdf+xml" in request.accept_mimetypes.best:
        g = Graph()
        g.parse(data=json.dumps(jsonData), format='json-ld')
        rdfxml = g.serialize(format='xml')
        return Response(rdfxml, mimetype='application/rdf+xml')
    
    return render_template("instance.html", jsonData=jsonData)
    

@app.route("/api/cedar/template.json")
def template():
    """
    Retrieve cedar template from the main repository,
    and pass it to the embeddable editor in the front-end
    """
    template = get_template()
    return Response(json.dumps(template), mimetype='application/json')

def get_template():
    """
    Get template from cedar itself, or from a local json-ld file
    In config.yaml file for local file:
    ```
    template:
        source: file
        location: template.json
    ```

    In config.yaml for cedar:
    ```
    template:
        source: cedar
        api_key: <your_api_key>
        templateId: <your_template_uuid>
    ```
    """
    if config['template']['source'] == 'cedar':
        response=None
        if "api_key" in config['template']:
            headers = {
                "Authorization": f"apiKey {config['template']['api_key']}",
                "Content-Type": "application/json"
            }
            response = requests.get(f"https://repo.metadatacenter.org/templates/{config['template']['templateId']}", headers=headers)
        else:
            response = requests.get(f"https://open.metadatacenter.org/templates/https:%2F%2Frepo.metadatacenter.org%2Ftemplates%2F{config['template']['templateId']}")

        return json.loads(response.text)
    
    if config['template']['source'] == 'file':
        template = { }
        if os.path.exists(config['template']['location']):
            with open(config['template']['location']) as f:
                template = json.load(f)
        return template

@app.route("/api/cedar/store", methods=["POST", "PUT"])
def store():
    """
    Function to store the actual data generated using the cedar embeddable editor.
    """
    template = get_template()

    data_to_store = request.get_json()
    data_to_store_meta = data_to_store["metadata"]
    data_to_store_info = data_to_store["info"]

    if "id" in data_to_store_info:
        data_to_store_meta["@id"] = data_to_store_info["id"]
        data_to_store_meta["schema:isBasedOn"] = data_to_store_info["isBasedOn"]
        data_to_store_meta["pav:createdOn"] = data_to_store_info["createdOn"]
        data_to_store_meta["pav:lastUpdatedOn"] = datetime.datetime.now(local_tz).isoformat()
    else:
        data_to_store_meta["schema:isBasedOn"] = template['@id']
        data_to_store_meta["pav:createdOn"] = datetime.datetime.now(local_tz).isoformat()
        data_to_store_meta["pav:lastUpdatedOn"] = datetime.datetime.now(local_tz).isoformat()
    data_to_store["metadata"] = data_to_store_meta
    
    persistance.save_instance(data_to_store_meta)

    return {"message": "Hi there!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)