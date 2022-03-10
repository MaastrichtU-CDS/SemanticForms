from operator import truediv
from flask import Flask, Response, request, render_template
from flask_cors import CORS
import yaml
import os
import requests
import uuid
import json
from rdflib import Graph
import logging
import sys

app = Flask(__name__)
CORS(app)

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cedar/template.json")
def template():
    """
    Retrieve cedar template from the main repository,
    and pass it to the embeddable editor in the front-end
    """
    headers = {
        "Authorization": f"apiKey {config['cedar']['apiKey']}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"https://repo.metadatacenter.org/templates/{config['cedar']['templateId']}", headers=headers)
    return Response(response.text, mimetype='application/json')

@app.route("/api/cedar/store", methods=["POST", "PUT"])
def store():
    """
    Function to store the actual data generated using the cedar embeddable editor.
    """
    session_id = uuid.uuid4()
    if request.method == "PUT":
        session_id = request.args.get("id")
    
    fileNameJson = os.path.join(config['server']['storageFolder'], f"{session_id}.jsonld")
    fileNameTurtle = os.path.join(config['server']['storageFolder'], f"{session_id}.ttl")

    data_to_store = request.get_json()
    data_to_store = data_to_store["metadata"]
    data_to_store["schema:isBasedOn"] = f"https://repo.metadatacenter.org/templates/{config['cedar']['templateId']}"
    data_to_store["@id"] = f"http://localhost/template-instances/{session_id}"

    with open(fileNameJson, "w") as f:
        json.dump(data_to_store, f, indent=4)
    
    g = Graph()
    g.parse(data=json.dumps(data_to_store), format='json-ld')
    g.serialize(destination=fileNameTurtle)

    return {"id": f"{session_id}"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)