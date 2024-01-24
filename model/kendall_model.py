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
import pandas as pd

class Kendall(mesa.Model):
    def __init__(self,config):
        super().__init__()

        self.config = config
        self.agents = defaultdict(list)

        #set global seed
        self._set_global_seed(self.config.seed)

        #init network
        self.network = RoadNetwork(road_file=self.config.road_file, crs=self.config.crs, orig_crs=self.config.orig_crs)

        #initialize model
        self.set_space_and_schedule()

        #initialize agents
        self.init_agents()

        #initialize datacollector
        self.datacollector = DataCollector(self)
        self.datacollector.register("demand_gap", record=True)
        self.datacollector.register("demand_weight", record=False)
        self.datacollector.register("resident_profile", record=False)
        self.datacollector.register("supply_list", record=True)
        self.datacollector.register("endowment", record=False)
        self.datacollector.register("profit", record=False)
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
            self.schedule.add(building)
            if bld in project_list:
                project = Project(self.next_id(), model=self, building= building, 
                                 config= self.config.project_config,render=True)
                building.project = project
                self.agents[Project].append(project)
                self.schedule.add(project)
            building.reorganize()
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
        resident = Resident(self.next_id(), model=self, geometry=None, 
                            config=self.config.resident_config,house=house,office=office,render=False)
        self.schedule.add(resident)
        self.space.add_commuter(resident)
        self.agents[Resident].append(resident)
        return resident
    
    def collect_data(self):
        self.demand_list = defaultdict(float)
        self.demand_gap = defaultdict(float)
        self.demand_weight = defaultdict(float)
        self.resident_profile = defaultdict(int)
        self.supply_list = defaultdict(float)
        self.profit = defaultdict(int)
        self.endowment = 0
        num_resident = len(self.agents[Resident])

        for resident in self.agents[Resident]:
            for idx,category in enumerate(self.config.amenity_list):
                self.demand_weight[category] += resident.demand_weight[category]
                self.supply_list[category] += resident.supply_list[category]
                self.resident_profile[resident.profile] += 1
        
        for idx,category in enumerate(self.config.amenity_list):
            self.demand_list[category] = self.config.resident_config.demand_list[idx]*num_resident
            self.demand_gap[category] = max((self.demand_list[category]-self.supply_list[category]),0)

        for project in self.agents[Project]:
            if hasattr(project,"endowment"):
                self.endowment += project.endowment
        for developer in self.agents[Developer]:
            self.profit[developer.unique_id] = developer.profit
   

    #load agents from gis files
    def _load_from_file(self, file:str, agent_class:mg.GeoAgent, id_key:str="index"):
        agentcreator = mg.AgentCreator(agent_class=agent_class, model=self, crs=self.config.crs)
        if file.endswith('.json'):
            agents = agentcreator.from_GeoJSON(open(file).read())
        else:
            agents = agentcreator.from_file(file, unique_id=id_key)
        self.current_id = len(agents)
        return agents

    def _set_global_seed(self, seed):
        np.random.seed(seed)
        random.seed(seed)
    
    def step(self):
        # self.schedule.step_type(Building)
        self.schedule.step_type(Resident)
        self.schedule.step_type(Project)
        self.schedule.step_type(Developer)
        self.schedule.step_count()
        self.datacollector.collect_data()

if __name__ == "__main__":
    from util import global_config
    model = Kendall(config=global_config)
    # model.step()
    num_built_project = 0
    while num_built_project < len(model.agents[Project]):
        model.step()
        num_built_project = len([x for x in model.agents[Project] if x.status == 'built'])
    print("done!")