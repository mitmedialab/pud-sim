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
        self.building_plan = defaultdict(int)
        self.new_floors = defaultdict(list)
        self.max_profit_per_floor = np.max(config.profit_list)*self.footprint_area
        self.max_profit = config.max_buildable_floors*self.max_profit_per_floor
        self.profit = 0
        self.reward_profit = 0
        self.endowment = 0
        self.status = 'pending'
        super().__init__(unique_id, model, self.geometry , crs)

    #sum the demand gap from nearby residents
    def cal_demand_list(self):
        self.demand_gap = defaultdict(int)
        self.demand_weight = defaultdict(float)
        self.num_resident = len(self.building.neighbor[Resident])
        for resident in self.building.neighbor[Resident]:
            for key in self.config.amenity_list:
                self.demand_gap[key] += resident.demand_gap[key]
                self.demand_weight[key] += resident.demand_weight[key]/(self.num_resident+1)

    #calculate incentive for different amenities based on demand gap
    def cal_buildable_floors(self):
        #calculate incentive for different amenities based on demand gap
        self.incentive = defaultdict(float)
        self.expected_profit = defaultdict(float)
        self.buildable_floor = None

        mean_profit = np.mean(self.config.profit_list)    

        #expected profit = profit + incentive*max_profit
        for idx, category in enumerate(self.config.amenity_list):
            if self.demand_gap[category] > 0:
                self.incentive[category] = self.config.incentive_ratio*self.demand_weight[category]
                profit = self.config.profit_list[idx]*self.footprint_area
                reward_profit = self.incentive[category]*mean_profit*self.footprint_area
                self.expected_profit[category] = {"profit":profit,"reward_profit":reward_profit,"total":profit+reward_profit}
        
        #rank exptected profit and choose the category with highest profit first
        ranked_profit_list = sorted(self.expected_profit.keys(), key=lambda x: self.expected_profit[x]["total"], reverse=True)
        if len(ranked_profit_list):
            category = ranked_profit_list[0]
            #calculate reward_profit
            expexted_profit = self.expected_profit[category]["profit"]
            expected_reward_profit = self.expected_profit[category]["reward_profit"]
            if (self.profit + expexted_profit + expected_reward_profit) < self.max_profit:
                self.buildable_floor = category
                
        
    def prepare_to_build(self):
        self.cal_demand_list()
        self.cal_buildable_floors()
            
    #build floor step by step
    def build(self):
        if self.status == 'building':
            if self.buildable_floor:
                category = self.buildable_floor
                self.building_plan[category] += 1
                self.building.add_floor(category=category)
                self.profit += self.expected_profit[category]["total"]
                self.reward_profit += self.expected_profit[category]["reward_profit"]
                self.endowment += self.expected_profit[category]["profit"]*self.config.endowment_ratio/self.num_resident
                #build reward floor
                if self.reward_profit >= self.max_profit_per_floor:
                    category = random.choice(["Office","Housing"])
                    self.building_plan[category] += 1
                    self.building.add_floor(category=category)
                    self.reward_profit -= self.max_profit_per_floor
            else:
                self.status = 'built'
        
        # print("_____________________________________")
        # print("project:",self.unique_id)
        # print("status:",self.status)
        # print("category to build:",self.buildable_floor)
        # print("profit:",self.profit)
        # print("max_profit:",self.max_profit)
        # print("_____________________________________")

    def parallel_step(self):
        self.prepare_to_build()
        pass

    def step(self):
        # self.prepare_to_build()
        self.build()
        pass
