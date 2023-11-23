
import mesa
from agent.kendall_agents import *
from model.kendall_model import Kendall
from shapely.geometry import mapping
from flask import Flask,jsonify
from flask_cors import CORS
import os,sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

app = Flask(__name__)
CORS(app)

model = None
floor_data = None
project_data = None
path_data = None

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
    "crs" : "epsg:4326"
    }

#Agent Style
def agent_property(agent):
    properties = {}
    if isinstance(agent, Floor):
        properties["category"] = agent.Category
        properties["area"] = agent.area
        properties["floor"] = agent.floor
        properties["ind"] = agent.ind
        properties["new"] = agent.new
        properties["type"] = "floor"

    if isinstance(agent, Project):
        properties["developer"] = agent.developer.unique_id
        properties["height"] = agent.height
        properties["type"] = "project"

    return properties

def _render_agents(model,properties_method=None):
    floor_data = {"type": "FeatureCollection", "features": []}
    project_data = {"type": "FeatureCollection", "features": []}    
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
            if type(agent) == Project:
                project_data["features"].append(data)
                
        if type(agent) == Resident:
            path_data.append({"path":agent.my_path,"timestamps":[i for i in range(len(agent.my_path))]})
            
    return floor_data,project_data,path_data

@app.route('/init')
def run():
    return jsonify({'floor_data':init_floor,'project_data':init_project,'path_data':init_path})

@app.route('/path_data')
def init():
    return jsonify(path_data)

@app.route('/floor_data')
def get_floor_data():
    global floor_data
    return jsonify(floor_data)

@app.route('/project_data')
def get_project_data():
    global project_data
    return jsonify(project_data)
    
@app.route('/step')
def step():
    global model,floor_data, project_data, path_data
    model.step()
    floor_data, project_data, path_data= _render_agents(model, properties_method=agent_property)
    return jsonify({'floor_data':floor_data,'project_data':project_data,'path_data':path_data})

@app.route('/reset')
def reset(model_params=model_params):
    global model,init_floor,init_project,init_path
    model = Kendall(**model_params)
    init_floor,init_project,init_path = _render_agents(model, properties_method=agent_property)
    model.step()
    return jsonify('model reset')


if __name__ == '__main__':

    model = Kendall(**model_params)
    init_floor,init_project,init_path = _render_agents(model, properties_method=agent_property)
    model.step()
    print("Model loaded")
    app.run(host='0.0.0.0',debug=True, port=5001, use_reloader=False)

    # import time
    # for i in range(100):
    #     start = time.time()
    #     model.step()
    #     stop = time.time()
    #     print(stop-start)