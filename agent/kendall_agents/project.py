import mesa_geo as mg
from .floor import Floor
from .resident import Resident
import numpy as np
import random
import math
from collections import defaultdict,Counter

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
        self.building_plan = defaultdict(int)
        self.new_floors = defaultdict(list)
        self.building_idx = 0
        self.max_profit = config.max_buildable_floors*np.max(config.profit_list)*self.footprint_area
        self.status = 'pending'
        super().__init__(unique_id, model, self.geometry , crs)

    #sum the demand gap from nearby residents
    def cal_demand_list(self):
        self.demand_gap = defaultdict(int)
        self.demand_weight = defaultdict(float)
        num_resident = len(self.building.neighbor[Resident])
        for resident in self.building.neighbor[Resident]:
            for key in self.config.amenity_list:
                self.demand_gap[key] += resident.demand_gap[key]
                self.demand_weight[key] += resident.demand_weight[key]/num_resident

    #calculate incentive for different amenities based on demand gap
    def cal_buildable_floors(self):
        #calculate incentive for different amenities based on demand gap
        self.incentive = defaultdict(float)
        self.expected_profit = defaultdict(float)
        self.profit = 0
        self.endowment = 0
        self.reward_floor = 0
        self.reward_profit = 0
        self.buildable_floors = []

        max_profit = np.max(self.config.profit_list)    

        #expected profit = profit + incentive*mean_profit
        for idx, category in enumerate(self.config.amenity_list):
            self.incentive[category] = self.config.incentive_ratio*self.demand_weight[category]
            profit = self.config.profit_list[idx]
            reward_profit = self.incentive[category]*max_profit
            self.expected_profit[category] = profit + reward_profit
        
        #rank exptected profit and choose the category with highest profit first
        ranked_profit_list = sorted(self.expected_profit.keys(), key=lambda x: self.expected_profit[x] , reverse=True)
        for category in ranked_profit_list:
            for i in range(math.ceil(self.demand_gap[category]/self.footprint_area)):
                if self.profit < self.max_profit:
                    idx = self.config.amenity_list.index(category)
                    profit = self.config.profit_list[idx]*self.footprint_area
                    reward_profit = self.incentive[category]*max_profit*self.footprint_area
                    self.reward_profit += reward_profit
                    self.profit += (profit+reward_profit)
                    #add demand floor
                    self.buildable_floors.append(category)
        
        reward_area = self.reward_profit/max_profit
        reward_floor = math.ceil(reward_area/self.footprint_area)
        for j in range(reward_floor):
            # add reward floor
            category = random.choice(["Office","Housing"])
            self.buildable_floors.append(category)
        
        # calculate the endowment and final profit
        self.endowment = self.profit*self.config.endowment_ratio
        self.profit = self.profit - self.endowment
    
    def prepare_to_build(self):
        self.cal_demand_list()
        self.cal_buildable_floors()
            
    #build floor step by step
    def build(self):
        if self.status == 'building':
            if len(self.buildable_floors):
                category = self.buildable_floors[0]
                self.building_plan[category] += 1
                floor = self.building.add_floor(category=category)
                self.new_floors[category].append(floor)
                # self.building_idx += 1
            else:
                self.status = 'built'
            
    def parallel_step(self):
        # self.prepare_to_build()
        pass

    def step(self):
        self.prepare_to_build()
        self.build()
        pass
