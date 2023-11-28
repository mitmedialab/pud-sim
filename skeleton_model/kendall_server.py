
import mesa
from agent.kendall_agents import *
from model.kendall_model import Kendall
from shapely.geometry import mapping
from flask import Flask,jsonify,request
from flask_cors import CORS
import os,sys
import json

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

app = Flask(__name__)
CORS(app)

model = None

model_params ={
    "agent_class": {
        'floors' : Floor,
        'projects' : Project,
        'residents' : Resident,
        'developers' : Developer,
    },
    "geo_file": os.path.join(dir_path,'data/kendall_buildings.json'),
    "road_file": os.path.join(dir_path,"data/kendall_roads.shp"),
    "population": 1000,
    "developer_num": 5,
    "crs" : "epsg:4326",
    "init_incentive":{
        "workforce_housing":0.4,
        "early_career_housing":0.4,
        "executive_housing":0.1,
        "family_housing":0.3,
        "senior_housing":0.2,
        "office_lab":0,
        "daycare":0.6,
        "phamacy":0.2,
        "grocery":0.3,
    }
    }

#Agent Style
def get_agent_property(agent):
    properties = {}
    if isinstance(agent, Floor):
        properties["category"] = agent.Category
        properties["floor"] = agent.floor
        properties["ind"] = agent.ind
        properties["new"] = agent.new
        properties["is_project"] = agent.is_project
        properties["type"] = "floor"
    return properties

def get_geojson(model,properties_method=None):
    floor_data = {"type": "FeatureCollection", "features": []} 
    path_data = []
    for agent in model.space.agents:
        if agent.render:
            transformed_geometry = agent.get_transformed_geometry(
                model.space.transformer
            )
            properties = {}
            if properties_method:
                properties = properties_method(agent)
            data = {
                    "type": "Feature",
                    "geometry": mapping(transformed_geometry),
                    "properties": properties,
                    }
            if type(agent) == Floor:
                floor_data["features"].append(data)
        if type(agent) == Resident:
            path_data.append({"path":agent.my_path,"timestamps":[i for i in range(len(agent.my_path))]})

    return jsonify({'floor_data':floor_data,
                    'path_data':path_data,
                    'collected_data':model.datacollector.data,
                    })

@app.route('/init')
def run():
    return get_geojson(model,properties_method=get_agent_property)
    
@app.route('/step')
def step():
    global model
    model.step()
    return get_geojson(model,properties_method=get_agent_property)

@app.route('/reset',methods=['POST','GET'])
def reset(model_params=model_params):
    global model
    model_params_ = model_params
    if request.method == 'POST':
        model_params_["init_incentive"] = request.get_json()
    model = Kendall(**model_params)
    return get_geojson(model,properties_method=get_agent_property)

if __name__ == '__main__':

    model = Kendall(**model_params)
    print("Model loaded")
    app.run(host='0.0.0.0',debug=True, port=5001, use_reloader=False)

    # import time
    # for i in range(100):
    #     start = time.time()
    #     model.step()
    #     stop = time.time()
    #     print(stop-start)