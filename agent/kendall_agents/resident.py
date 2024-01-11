import numpy as np
from agent import BDIAgent,Commuter
from .floor import Floor
from shapely.geometry import Point
import random
from itertools import groupby
from util import point_in_polygon
from collections import defaultdict

class Resident(Commuter, BDIAgent):
    def __init__(self, unique_id, model, geometry, config, crs=None, render=True, house=None, office=None):
        if not crs:
            crs = model.space.crs
        Commuter.__init__(self,unique_id, model, geometry, crs)
        BDIAgent.__init__(self,unique_id, model)
        self.config = config
        self.render = render
        self.demand_gap = defaultdict(int)
        self.demand_weight = defaultdict(float)
        self.init_agent(house,office)
    
    # def _random_point_in_polygon(self,polygon):
    #     minx, miny, maxx, maxy = polygon.bounds
    #     offset = min(maxx-minx,maxy-miny)*0.2
    #     z = polygon.exterior.coords[0][2]
    #     while True:
    #         pnt = Point(np.random.uniform(minx+offset, maxx-offset), np.random.uniform(miny+offset, maxy-offset),z)
    #         if polygon.contains(pnt):
    #             break
    #     return pnt

    def init_agent(self, house=None, office=None):
        if not house:
            house = self.model.get_random_house()
        if not office:
            office = self.model.get_random_office()
        self.building = house.building
        type = list(self.config.resident_types_ratio.keys())
        ratio = list(self.config.resident_types_ratio.values())
        self.profile = random.choices(type,weights=ratio)[0]
        #set demand weight
        for idx,key in enumerate(self.config.amenity_list):
            self.demand_weight[key] = self.config.demand_weight[self.profile][idx]
        #set house & office
        self.house = point_in_polygon(house.geometry,random=True)
        self.office = point_in_polygon(office.geometry,random=True)
        self.geometry = self.house
        self.cal_commute_path()

    # calculate supply of different amenities in the neighborhood
    def cal_supply(self):
        self.supply_list = {}
        for category in self.config.amenity_list:
            self.supply_list[category] = 0
        for category, floors in groupby(self.building.neighbor[Floor], lambda x: x.Category):
            if category in self.config.amenity_list:
                self.supply_list[category] = sum([float(floor.area) for floor in floors])//(len(self.building.neighbor[Resident])+1)
    
    # calculate demand gap of different amenities
    def cal_demand_gap(self):
        self.demand_gap = {}
        for idx,key in enumerate(self.config.amenity_list):
            self.demand_gap[key] = max(self.config.demand_list[idx] - self.supply_list[key],0)

    def cal_commute_path(self):
        self.origin = (self.office.x,self.office.y)
        self.destination = (self.house.x,self.house.y)
        self._prepare_to_move(self.origin,self.destination)

    def parallel_step(self):
        self.cal_supply()
        self.cal_demand_gap()
        pass
        
    def step(self):
        pass
        