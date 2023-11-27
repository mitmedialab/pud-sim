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
from model import DataCollector
from mesa.time import RandomActivation
from itertools import groupby
from shapely.geometry import Polygon

class Kendall(mesa.Model):
    def __init__(self,
                 agent_class:dict,
                 geo_file:str,
                 population:int,
                 developer_num:int,
                 init_incentive:dict,
                 road_file:str = None,
                 crs:str ='epsg:4326'):
        super().__init__()

        self.agent_class = agent_class
        self.geo_file = geo_file
        self.population = population
        self.developer_num = developer_num
        self.incentive = init_incentive
        self.buildings = []
        self.projects = []
        self.developers = []
        self.residents = []
        self.vote_list = None
        self.crs = crs
        
        #init network
        self.network = RoadNetwork(road_file=road_file, crs=crs)

        #initialize model
        self.set_space_and_schedule()

        #initialize agents
        self.init_agents()

        #initialize incentive, developer balance and profit
        self.update_incentive()

        #initialize datacollector
        self.datacollector = DataCollector(self)
        self.datacollector.register("incentive", record=True)
        self.datacollector.register("vote_list", record=False)
        self.datacollector.register("expenditures", record=False)
        self.datacollector.register("profits", record=False)
        
        #init vote list
        self.call_for_vote()
        self.datacollector.collect_data()
    
    #initialize space and schedule
    def set_space_and_schedule(self):
        self.space = CommuteSpace(crs=self.crs,warn_crs_conversion=False)
        self.schedule = ParallelActivation(self)
    
    def init_agents(self):
        #floors
        self.floors = self._load_from_file('floors', self.geo_file, self.agent_class['floors'])

        #buildings
        buildings_ = groupby(self.floors, lambda x: x.bld)
        for bld, floors in tqdm(buildings_, "create buildings"):
            building = Building(self.next_id(), self, list(floors), bld, render=False)
            self.buildings.append(building)

        #developers and projects (added to schedule)
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
                project = Project(self.next_id(), self, building_, geometry=Polygon(shell=new_coords),render=False)
                developer = random.choice(self.developers)
                developer.add_project(project)
                project.developer = developer
                self.projects.append(project)
                # don't need add project to schedule for now 
                # self.schedule.add(project)
            self.space.add_agents(self.projects) 

        #init developer's project
        for developer in self.developers:
            developer.choose_project()
        
        potential_house_ = [x for x in self.floors if x.Category in ["Residential","Mixed Use Residential"]]
        potential_office_ = [x for x in self.floors if x.Category not in ["Residential","Mixed Use Residential"]]
        
        #residents
        for j in tqdm(range(self.population),"create residents"):
            house = random.choices(potential_house_, weights=[x.area for x in potential_house_], k=10)[0]
            office = random.choices(potential_office_, weights=[x.area for x in potential_office_], k=10)[0]
            resident = Resident(self.next_id(), self, None, self.crs)
            resident.set_house(house)
            resident.set_office(office)
            resident.prepare_to_move()
            self.residents.append(resident)
            # don't need add resident to schedule for now
            # self.schedule.add(resident) 
            self.space.add_commuter(resident)
    
    def update_incentive(self):
        incentive = {}
        for resident in self.residents:
            for key in resident.desire_base.keys():
                if key not in incentive.keys():
                    incentive[key] = []
                incentive[key].append(resident.desire_base[key].intensity)
        for key in incentive.keys():
            incentive[key] = max(np.mean(incentive[key]),0)
        self.incentive = incentive
        self.expenditures = [x.expenditure for x in self.developers]
        self.profits = [x.profit for x in self.developers]
        return self.incentive
    
    def call_for_vote(self):
        vote_list = []
        for resident in self.residents:
            vote = resident.vote()
            vote_list.append(vote)
        self.vote_list = dict(Counter(vote_list))


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
        self.call_for_vote()
        self.schedule.step()
        self.update_incentive()
        self.datacollector.collect_data()


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