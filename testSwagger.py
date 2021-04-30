import json
import numpy as np
from flask import Flask, request, jsonify
from flasgger import Swagger
from flasgger.utils import swag_from
from flasgger import LazyString, LazyJSONEncoder
from flask import Flask, render_template,request,redirect,url_for,jsonify
import json
import cognitive_face as CF
import requests
import pymongo
import pandas as pd
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import azure.cosmos.errors as errors
import azure.cosmos.documents as documents
import azure.cosmos.http_constants as http_constants
#import http.client, urllib.request, urllib.parse, urllib.error, base64
from flask import Response
from datetime import datetime
from flask_cors import CORS


app = Flask(__name__)
app.config["SWAGGER"] = {"title": "Swagger-UI", "uiversion": 2}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "https://stagingenvnodesequencer.scenera.live",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)

app.json_encoder = LazyJSONEncoder
swagger = Swagger(app, config=swagger_config, template=template)


@app.route("/")
def index():
    return "setSceneMark"


@app.route("/setSceneMark", methods=["POST"])
@swag_from("swagger_config.yml")
def add_numbers():
    scenemark_file = request.json
    try:
        uri = "mongodb://face-recognition-1:mgT6eNYp88f25HL4JogVsH20KznhvuhKg92aJzpK9lNB3A1RVhiKWA0MVwXDRFewd2hIVNXN4ECnnSan4CB7iA==@face-recognition-1.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@face-recognition-1@"
        myclient = pymongo.MongoClient(uri)
        mydb = myclient["New_face"]
        mycol = mydb["faceInfo"]

        scenemark_file["scenemarks"]["Payload"]["Body"] = scenemark_file["scenemarks"]["Payload"]["Body"].replace('\\"',"\"")
        print(scenemark_file)

        #scenemark_file = json.loads(scenemark_file)
        scenemark_file["scenemarks"]["Payload"]["Body"] = json.loads(scenemark_file["scenemarks"]["Payload"]["Body"])

        img_url = []
        for i in scenemark_file["scenemarks"]["Payload"]["Body"]['SceneDataList']:
            img_url.append(i['SceneDataURI'])
        print(img_url)

        users = mycol.find()
        x =  pd.DataFrame(list(users))

        x = x[x['Active']==True]
        x = x.reset_index(drop=True)

        ############# Perform the Face Detection############
        face_api_url_verify = 'https://facedemonstration.cognitiveservices.azure.com/face/v1.0/verify'
        subscription_key = "055cc8b8d56c42e5bddc8e8a315c080d"

        faceURI = "https://facedemonstration.cognitiveservices.azure.com/face/v1.0/"
        faceKey = "055cc8b8d56c42e5bddc8e8a315c080d"

        CF.BaseUrl.set(faceURI)
        CF.Key.set(faceKey)

        def face_compare(id_1,personGroupId,personId,url):

            headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': subscription_key
            }

            body = {"faceId": id_1, "personGroupId": personGroupId,"personId":personId}
            #print(body)
            params = {}
            response = requests.post(url,
                                    params=params,
                                    headers=headers,
                                    json=body)

            res = response.json()
            return res


        face1 = []
        #print("Outside loop")
        for i in range(len(img_url)):
            #print("inside loop")
            result = CF.face.detect(img_url[i])
            face1.append(result[0]['faceId'])
        print(face1)

        for i in range(len(face1)):
            print(i)
            for j in range(len(x['personId'])):
                print(j)
                a =face_compare(face1[i],x['personGroupId'][j],x['personId'][j],face_api_url_verify)
                print(a)

                if(a['isIdentical'] == True):
                    users = mycol.find()
                    users =  pd.DataFrame(list(users))
                    users = users[users['personId']==x['personId'][j]]
                    print(users)
                    name = users['name']
                    name = name.item()
                    scenemark_file["scenemarks"]["Payload"]["Body"]['SceneDataList'][i]['name'] = name
                elif(a['isIdentical'] == False):
                    scenemark_file["scenemarks"]["Payload"]["Body"]['SceneDataList'][i]['name'] = "NULL"
        return scenemark_file
    except:
        res = {"success": False, "message": "Unknown error"}


if __name__ == "__main__":
    app.run(debug=True)
