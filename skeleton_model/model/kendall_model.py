# import sys,os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mesa
import mesa_geo as mg
from agent.kendall_agents import *
from tqdm import tqdm
import numpy as np
import random
from schedule import ParallelActivation
from space import RoadNetwork,CommuteSpace
from mesa.time import RandomActivation
from itertools import groupby
from shapely.geometry import Polygon

class Kendall(mesa.Model):
    def __init__(self,
                 agent_class:dict,
                 geo_file:str,
                 population:int,
                 developer_num:int,
                 road_file:str = None,
                 crs:str ='epsg:4326'):
        super().__init__()

        self.agent_class = agent_class
        self.geo_file = geo_file
        self.population = population
        self.developer_num = developer_num
        self.buildings = []
        self.projects = []
        self.developers = []
        self.crs = crs
        
        #init network
        self.network = RoadNetwork(road_file=road_file, crs=crs)

        #initialize model
        self.set_space_and_schedule()

        #initialize agents
        self.init_agents()
    
    #initialize space and schedule
    def set_space_and_schedule(self):
        self.space = CommuteSpace(crs=self.crs,warn_crs_conversion=False)
        self.schedule = ParallelActivation(self)
    
    def init_agents(self):
        self._load_from_file('floors', self.geo_file, self.agent_class['floors'])
        buildings_ = groupby(self.floors, lambda x: x.bld)
        for bld, floors in tqdm(buildings_, "create buildings"):
            building = Building(self.next_id(), self, list(floors), bld, render=False)
            self.buildings.append(building)

        for i in tqdm(range(self.developer_num),"create developers"):
            developer = Developer(self.next_id(), self, render=False)
            self.developers.append(developer)
            self.schedule.add(developer)
        
        project_list = ["643-5","677-1","672-5","620-74",
                        "668-76","666-1","554-1","708-18",
                        "625-1","606-2","620-88","610-7",
                        "606-1","668-14","728-3","496-1"]
    
        for building_ in tqdm(self.buildings,"create projects"):
            if building_.bld in project_list:
                
                geometry = building_.floors[0].geometry
                _coords = [(x, y, 0) for x, y, z in list(geometry.exterior.coords)]
                new_coords = [(x, y, 0) for x, y, z in _coords]
                project = Project(self.next_id(), self, building_, geometry=Polygon(shell=new_coords),render=True)
                developer = random.choice(self.developers)
                developer.add_project(project)
                project.developer = developer
                self.projects.append(project) 
                self.schedule.add(project)
            self.space.add_agents(self.projects)  
        
        potential_house_ = [x for x in self.floors if x.Category in ["Residential","Mixed Use Residential"]]
        potential_office_ = [x for x in self.floors if x.Category not in ["Residential","Mixed Use Residential"]]

        for j in tqdm(range(self.population),"create residents"):
            house = random.choices(potential_house_, weights=[x.area for x in potential_house_], k=10)[0]
            office = random.choices(potential_office_, weights=[x.area for x in potential_office_], k=10)[0]
            resident = Resident(self.next_id(), self, None, self.crs)
            resident.set_house(house)
            resident.set_office(office)
            resident.prepare_to_move()
            self.schedule.add(resident)
            self.space.add_commuter(resident)

    #load agents from gis files
    def _load_from_file(self, key:str, file:str, agent_class:mg.GeoAgent, id_key:str="index"):
        agentcreator = mg.AgentCreator(agent_class=agent_class, model=self)
        if file.endswith('.json'):
            agents = agentcreator.from_GeoJSON(open(file).read())
        else:
            agents = agentcreator.from_file(file, unique_id=id_key)
        self.space.add_agents(agents)
        self.__setattr__(key,agents)
        self.current_id = len(agents)
        return agents
    
    def step(self):
        self.schedule.step()


if __name__ == "__main__":
    model_params ={
    "agent_class": {
        'floors' : Floor,
        'projects' : Project,
        'residents' : Resident,
        'developers' : Developer,
    },
    "geo_file": 'data/kendall_buildings.json',
    "road_file": "data/kendall_roads.shp",
    "population": 10,
    "developer_num": 10,
    }
    model = Kendall(**model_params)
    model.step()