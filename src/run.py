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
from endpoint_service import SPARQLEndpoint

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

# Create storage folder
if not os.path.exists(config['server']['storageFolder']):
    os.makedirs(config['server']['storageFolder'])

sparqlEndpoint = SPARQLEndpoint(config["server"]["server_url"], config["server"]["repository_name"], update_endpoint_suffix=config["server"]["update_endpoint_suffix"])

@app.route("/")
def index():
    instances = sparqlEndpoint.list_instances(titlePredicate=config["template"]["title_predicate"])
    for idx, val in enumerate(instances):
        if "title" not in instances[idx]:
            instances[idx]["title"] = {
                "value": instances[idx]["instance"]["value"].replace(config["template"]["instance_base_url"] + "/", ""),
                "type": "literal"
            }
    
    
    if config["template"]["storage"]=="cedar":
        return render_template("index.html", instances=instances, template_id=config["template"]["templateId"])
    else:
        return render_template("index.html", instances=instances)

@app.route("/add")
def cee():
    return render_template("cee.html", templateObject=json.dumps(get_template()))

@app.route("/edit")
def edit_cee():
    identifier = None
    if "uri" in request.args:
        identifier = request.args.get("uri").replace(config['template']['instance_base_url'], ".")
    jsonData = None
    
    if identifier:
        fileNameJson = os.path.join(config['server']['storageFolder'], f"{identifier}.jsonld")
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
        return render_template("cee.html",
                               templateObject=json.dumps(get_template()),
                               formData=json.dumps(jsonData),
                               formInfo=json.dumps(infoData))
    
    return redirect("/", error="Could not load data")  

@app.route("/delete")
def delete_instance():
    identifier = request.args.get("uri")
    sparqlEndpoint.drop_instance(identifier)
    return redirect("/")

@app.route("/instance")
def showInstance():
    identifier = request.args.get("uri")
    properties = sparqlEndpoint.describe_instance(identifier)
    references = sparqlEndpoint.get_instance_links(identifier)
    return render_template("instance.html", properties=properties, references=references, instance_uri=identifier)

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
    
    fileNameJson = None
    target = data_to_store_meta
    
    if request.method == "POST":
        session_id = uuid.uuid4()
        print("new profile")
        print(f"Session id: {session_id}")

        fileNameJson = os.path.join(config['server']['storageFolder'], f"{session_id}.jsonld")
        target["schema:isBasedOn"] = template['@id']
        target["pav:createdOn"] = datetime.datetime.now(local_tz).isoformat()
        target["@id"] = f"{config['template']['instance_base_url']}/{session_id}"
    else:
        data_to_store_info = data_to_store["info"]
        fileNameJson = data_to_store_info['fileName']
        print("existing profile")
        target["@id"] = data_to_store_info["id"]
        target["schema:isBasedOn"] = data_to_store_info["isBasedOn"]
        target["pav:createdOn"] = data_to_store_info["createdOn"]
        target["pav:lastUpdatedOn"] = datetime.datetime.now(local_tz).isoformat()
    
    with open(fileNameJson, "w") as f:
        # print(json.dumps(target, indent=4))
        json.dump(target, f, indent=4)

    fileNameTurtle = fileNameJson.replace(".jsonld", ".ttl")
    g = Graph()
    g.parse(data=json.dumps(target), format='json-ld')
    g.serialize(destination=fileNameTurtle)
    
    turtleData = g.serialize(format='nt')
    sparqlEndpoint.store_instance(turtleData, target["@id"])

    return {"message": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)