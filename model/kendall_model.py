# import sys,os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mesa
import mesa_geo as mg
from agent.kendall_agents import Floor, Building, Project, Resident
from tqdm import tqdm
import numpy as np
import random
from schedule import ParallelActivation
from space import RoadNetwork,CommuteSpace
from model import DataCollector
from itertools import groupby
from shapely.geometry import Polygon

class Kendall(mesa.Model):
    def __init__(self,config):
        super().__init__()

        self.config = config
        self.buildings = [] 
        self.projects = []
        self.residents = []

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
        self.schedule = ParallelActivation(self)
    
    def init_agents(self):
        #floors
        self.floors = tqdm(self._load_from_file(self.config.geo_file, Floor),"create floors")

        #buildings and projects
        project_list = self.config.project_list
        buildings_ = groupby(self.floors, lambda x: x.bld)
        for bld, floors in tqdm(buildings_,"create buildings"):
            building = Building(self.next_id(), model=self, floors=list(floors), 
                                bld = bld, config = self.config.building_config, render=False)
            self.buildings.append(building)
            if bld in project_list:
                project = Project(self.next_id(), model=self, building= building, 
                                 config= self.config.project_config,render=False)
                self.projects.append(project)

        #residents
        potential_house_ = [x for x in self.floors if x.Category =='Housing']
        potential_office_ = [x for x in self.floors if x.Category == 'Office' ]
        for j in tqdm(range(self.config.population),"create residents"):
            house = random.choices(potential_house_, weights=[float(x.area) for x in potential_house_], k=10)[0]
            office = random.choices(potential_office_, weights=[float(x.area) for x in potential_office_], k=10)[0]
            resident = Resident(self.next_id(), model=self, geometry=None, config=self.config.resident_config)
            resident.init_agent(house,office)
            self.residents.append(resident)
        for resident in tqdm(self.residents,"get neighbors for each resident"):
            self.space.add_commuter(resident)
            self.schedule.add(resident)
            resident.get_neighbors()
        
        #add agents to space and schedule
        self.space.add_agents(self.buildings)
        self.space.add_agents(self.projects)
        for project in tqdm(self.projects,"get residents for each projects"):
            self.schedule.add(project)
            project.get_residents()
        
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
        self.schedule.step()
        pass


if __name__ == "__main__":
    from util import global_config
    model = Kendall(config=global_config)
    model.step()