
import mesa
from agent.kendall_agents import Floor, Building, Project, Resident
from model.kendall_model import Kendall
from shapely.geometry import mapping
from flask import Flask,jsonify,request
from flask_cors import CORS
import os,sys
import json
from util import global_config

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

app = Flask(__name__)
CORS(app)

model = None

#Agent Style
def get_agent_property(agent):
    properties = {}
    if isinstance(agent, Floor):
        properties["category"] = agent.Category
        properties["floor"] = agent.floor
        properties["area"] = agent.area
        properties["bld"] = agent.bld
    if isinstance(agent, Project):
        properties["status"] = agent.status
        if hasattr(agent,"round"):
            properties["develop_round"] = agent.round
        if hasattr(agent,"expected_profit"):
            properties["expected_profit"] = agent.expected_profit
            properties["endowment"] = agent.endowment
        if hasattr(agent,"demand_gap"):
            properties["demand_gap"] = agent.demand_gap
    return properties

def get_agent_geometry(agent):
    if agent.render:
        transformed_geometry = agent.get_transformed_geometry(
            model.space.transformer
        )
        return mapping(transformed_geometry)

def get_geojson(model,geometry_method=get_agent_geometry,properties_method=get_agent_property):
    floor_data = {"type": "FeatureCollection", "features": []} 
    project_data = []
    path_data = []
    for agent in model.agents[Floor]:
        properties = properties_method(agent)
        geometry = geometry_method(agent)
        data = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
                "new" : agent.new,
                "is_project" : agent.is_project
                }
        floor_data["features"].append(data)
    
    for agent in model.agents[Project]:
        properties = properties_method(agent)
        geometry = geometry_method(agent)
        project_data.append({
            "coordinates":geometry["coordinates"],
            "properties": properties,
        })
    
    for agent in model.agents[Resident]:
        transformed_path = [model.space.transformer.transform(x, y) for x, y in agent.my_path]
        path_data.append({"path":transformed_path,"timestamps":[i for i in range(len(transformed_path))]})

    return jsonify({'floor_data':floor_data,
                    'project_data':project_data,
                    'path_data':path_data,
                    'collected_data':model.datacollector.data,
                    })

@app.route('/init')
def init():
    return get_geojson(model)
    
@app.route('/step')
def step():
    global model
    model.step()
    return get_geojson(model)

@app.route('/reset',methods=['POST','GET'])
def reset():
    global model
    model = Kendall(config=global_config)
    model.step()
    return get_geojson(model)

if __name__ == '__main__':

    model = Kendall(config=global_config)
    model.step()
    print("Model loaded")
    app.run(host='0.0.0.0',debug=True, port=5001, use_reloader=False)

    # import time
    # for i in range(100):
    #     start = time.time()
    #     model.step()
    #     stop = time.time()
    #     print(stop-start)