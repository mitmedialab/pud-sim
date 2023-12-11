import mesa
import mesa_geo as mg
import numpy as np
from agent import BDIAgent,Commuter
from .building import Floor,Building
from .project import Project
from shapely.geometry import Point
import random
from itertools import groupby


class Resident(Commuter, BDIAgent):
    def __init__(self, unique_id, model, geometry, config, crs=None, render=True):
        if not crs:
            crs = model.space.crs
        Commuter.__init__(self,unique_id, model, geometry, crs)
        BDIAgent.__init__(self,unique_id, model)

        self.config = config
        self.render = render
    
    def _random_point_in_polygon(self,polygon):
        minx, miny, maxx, maxy = polygon.bounds
        offset = min(maxx-minx,maxy-miny)*0.2
        z = polygon.exterior.coords[0][2]
        while True:
            pnt = Point(np.random.uniform(minx+offset, maxx-offset), np.random.uniform(miny+offset, maxy-offset),z)
            if polygon.contains(pnt):
                break
        return pnt

    def init_agent(self,house:Floor,office:Floor):
        type = list(self.config.resident_types_ratio.keys())
        ratio = list(self.config.resident_types_ratio.values())
        self.profile = random.choices(type,weights=ratio)[0]
        self.demand_weight = self.config.demand_weight[self.profile]
        #set house
        self.house = self._random_point_in_polygon(house.geometry)
        #set office
        self.office = self._random_point_in_polygon(office.geometry)
        self.geometry = Point(self.house.x,self.house.y)
        self.cal_commute_path()
    
    def get_neighbors(self):
        self.neighbors = self.model.space.get_neighbors_within_distance(self, self.config.life_circle_radius)
        self.neighbor_projects = []
        self.neighbor_floors = []
        self.neighbor_residents = []
        self.neighbor_buildings = []
        for neighbor in self.neighbors:
            if isinstance(neighbor, Building):
                self.neighbor_buildings.append(neighbor)
                for floor in neighbor.floors:
                    self.neighbor_floors.append(floor)
            elif isinstance(neighbor, Resident):
                self.neighbor_residents.append(neighbor)
            elif isinstance(neighbor, Project):
                self.neighbor_projects.append(neighbor)

    def cal_supply(self):
        self.supply_list = {}
        for category, floors in groupby(self.neighbor_floors, lambda x: x.Category):
            self.supply_list[category] = sum([float(floor.area) for floor in floors])/(len(self.neighbor_floors)+1)

    def cal_demand_gap(self):
        self.demand_gap = {}
        for key in self.config.demand_list.keys():
            self.demand_gap[key] = self.config.demand_list[key] - self.supply_list[key] 

    def cal_commute_path(self):
        self.origin = (self.office.x,self.office.y)
        self.destination = (self.house.x,self.house.y)
        self._prepare_to_move(self.origin,self.destination)
        return self.my_path 

        
    def parallel_step(self):
        self.cal_supply()
        self.cal_demand_gap()
        
    def step(self):
        pass