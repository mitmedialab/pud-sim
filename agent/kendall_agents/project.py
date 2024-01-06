import mesa_geo as mg
from .floor import Floor
from .resident import Resident
import numpy as np
import random
from collections import defaultdict

class Project(mg.GeoAgent):
    def __init__(self, unique_id, model, building,config, crs=None, render=True):
        if not crs:
            crs = model.space.crs
        self.config = config
        self.building = building
        self.geometry = building.geometry
        self.footprint_area = self.building.floors[0].area
        self.render = render 
        self.buildable_floors = []
        self.new_floors = defaultdict(list)
        self.building_idx = 0
        self.status = None
        super().__init__(unique_id, model, self.geometry , crs)
    
    def cal_basic_profit(self):
        total_area = np.sum([x.area for x in self.building.floors])
        self.basic_profit = total_area*np.mean(self.config.profit_list)

    #sum the demand gap from nearby residents
    def cal_demand_list(self):
        self.demand_gap = {}
        self.demand_weight = {}
        for resident in self.building.neighbor[Resident]:
            for key in self.config.amenity_list:
                if key not in self.demand_gap.keys():
                    self.demand_gap[key] = 0
                    self.demand_weight[key] = 0
                self.demand_gap[key] += resident.demand_gap[key]
                self.demand_weight[key] += resident.demand_weight[key]
    
    #calculate incentive for different amenities based on demand gap
    def cal_incentive(self):
        self.incentive = {}
        sorted_demand_weight = sorted(self.demand_weight.keys(), key=lambda k: self.demand_weight[k])
        for idx, category in enumerate(sorted_demand_weight):
            self.incentive[category] = self.config.incentive_list[idx]

    #calcaulte expected profit of different amenities
    def cal_expected_profit(self):
        self.expected_profit = 0
        self.endowment = 0
        self.reward_profit = 0
        for idx,category in enumerate(self.config.amenity_list):
            profit = self.config.profit_list[idx]*self.demand_gap[category]
            reward_profit = self.incentive[category]*self.basic_profit
            expected_profit = (profit+reward_profit)
            endowment = self.config.endowment_ratio*expected_profit
            self.expected_profit += expected_profit-endowment
            self.endowment += endowment
            self.reward_profit += reward_profit
    
    def cal_buildable_floors(self):
        for category,area in self.demand_gap.items():
            for i in range(int(area//self.footprint_area)):
                self.buildable_floors.append(category)
        self.buildable_floors = [x for x in self.demand_gap.keys() if self.demand_gap[x]>0]
        reward_area = self.reward_profit//np.max(self.config.profit_list)
        reward_floor = int(reward_area//self.footprint_area)
        for floor in range(reward_floor):
            category = random.choice(['Office','Housing'])
            self.buildable_floors.append(category)
    
    def prepare_to_build(self):
        if not self.status:
            self.cal_basic_profit()
            self.cal_demand_list()
            self.cal_incentive()
            self.cal_expected_profit()
            self.cal_buildable_floors()
            self.status = 'pending'
            
    #build floor step by step
    def build(self):
        if self.status == 'building':
            if self.building_idx < len(self.buildable_floors):
                category = self.buildable_floors[self.building_idx]
                floor = self.building.add_floor(category=category)
                self.new_floors[category].append(floor)
                self.building_idx += 1
            else:
                self.status = 'built'
            
    def parallel_step(self):
        self.prepare_to_build()
        pass

    def step(self):
        self.build()
        pass
