from .agent import *
from .model import *

def agent_portrayal(agent):
    portrayal = {}

    if type(agent) is Gold:
        portrayal["Color"] = "yellow"
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1

    elif type(agent) is Market:
        portrayal["Color"] = "red"
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1

    elif type(agent) is Miner:
        portrayal["Color"] = "blue"
        portrayal["Shape"] = "circle"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.5

    return portrayal

width = 10
height = 10
model_params = {
    "N": mesa.visualization.Slider("Number of Gold agents:",10,10,20,1),
    "M" : mesa.visualization.Slider("Number of Market agents:",1,1,2,1),
    "O" : mesa.visualization.Slider("Number of Miner agents:",5,5,10,1),
    "width": width,
    "height": height,
}


grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 500, 500)
server = mesa.visualization.ModularServer(Model,
                       [grid],
                       "Gold Mine",
                       model_params)
server.port = 8521 # The default
