
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
        properties["new"] = agent.new
        # if agent.is_project:
        #     for k,v in agent.demand_list.items():
        #         properties[k] = v
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
            transformed_path = [model.space.transformer.transform(x, y) for x, y in agent.my_path]
            path_data.append({"path":transformed_path,"timestamps":[i for i in range(len(transformed_path))]})

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
def reset():
    return get_geojson(model,properties_method=get_agent_property)

if __name__ == '__main__':

    model = Kendall(config=global_config)
    print("Model loaded")
    app.run(host='0.0.0.0',debug=True, port=5001, use_reloader=False)

    # import time
    # for i in range(100):
    #     start = time.time()
    #     model.step()
    #     stop = time.time()
    #     print(stop-start)