import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mesa
import mesa_geo as mg
from agent.kendall_agents import Floor, Building, Project, Resident,Developer   
from tqdm import tqdm
import numpy as np
import random
from schedule import ParallelActivation,ParallelActivationByType
from space import RoadNetwork,CommuteSpace
from model import DataCollector
from itertools import groupby
from shapely.geometry import Polygon
from collections import defaultdict

class Kendall(mesa.Model):
    def __init__(self,config):
        super().__init__()

        self.config = config
        self.agents = defaultdict(list)

        #init network
        self.network = RoadNetwork(road_file=self.config.road_file, crs=self.config.crs, orig_crs=self.config.orig_crs)

        #initialize model
        self.set_space_and_schedule()

        #initialize agents
        self.init_agents()

        #initialize datacollector
        self.datacollector = DataCollector(self)
        # self.datacollector.register("incentive", record=True)
        # self.datacollector.register("vote_list", record=False)
        # self.datacollector.register("expenditures", record=False)
        # self.datacollector.register("profits", record=False)
        self.datacollector.collect_data()   
    
    #initialize space and schedule
    def set_space_and_schedule(self):
        self.space = CommuteSpace(crs=self.config.crs,warn_crs_conversion=False)
        self.schedule = ParallelActivationByType(self)
    
    def init_agents(self):
        #floors
        self.agents[Floor] = self._load_from_file(self.config.geo_file, Floor)

        #buildings and projects
        project_list = self.config.project_list
        buildings_ = {bld: list(group) for bld, group in groupby(self.agents[Floor], lambda x: x.bld)}
        for bld, floors in tqdm(buildings_.items(),"create buildings"):
            building = Building(self.next_id(), model=self, floors=list(floors), 
                                bld = bld, config = self.config.building_config, render=False)
            self.agents[Building].append(building)
            if bld in project_list:
                project = Project(self.next_id(), model=self, building= building, 
                                 config= self.config.project_config,render=False)
                building.project = project
                self.agents[Project].append(project)
                self.schedule.add(project)
        self.space.add_agents(self.agents[Building])
        self.space.add_agents(self.agents[Project])
        
        #create residents
        population = sum([x.area for x in self.agents[Floor] if x.Category =='Housing'])//self.config.density
        for j in tqdm(range(population),"create residents"):
            self.add_resident()

        #create developer
        for i in tqdm(range(self.config.developer_num),"create developers"):
            developer = Developer(self.next_id(), model=self)
            self.agents[Developer].append(developer)
            self.schedule.add(developer)
        
        #get neighbors
        for building in tqdm(self.agents[Building],"get neighbors"):
            building.get_neighbors()
    
    def get_random_house(self):
        potential_house = [x for x in self.agents[Floor] if x.Category =='Housing']
        return random.choice(potential_house)
    
    def get_random_office(self):
        potential_office = [x for x in self.agents[Floor] if x.Category == 'Office' ]
        return random.choice(potential_office)

    def add_resident(self,house=None,office=None):
        resident = Resident(self.next_id(), model=self, geometry=None, config=self.config.resident_config,house=house,office=office)
        self.schedule.add(resident)
        self.space.add_commuter(resident)
        self.agents[Resident].append(resident)
        return resident
        
    #load agents from gis files
    def _load_from_file(self, file:str, agent_class:mg.GeoAgent, id_key:str="index"):
        agentcreator = mg.AgentCreator(agent_class=agent_class, model=self, crs=self.config.crs)
        if file.endswith('.json'):
            agents = agentcreator.from_GeoJSON(open(file).read())
        else:
            agents = agentcreator.from_file(file, unique_id=id_key)
        self.space.add_agents(agents)
        self.current_id = len(agents)
        return agents
    
    def step(self):
        self.schedule.step_type(Resident)
        self.schedule.step_type(Project)
        self.schedule.step_type(Developer,shuffle=True)


if __name__ == "__main__":
    from util import global_config
    model = Kendall(config=global_config)
    for i in range(5):
        print("Step:",model.schedule.steps)
        model.step()
    print("done!")