import mesa_geo as mg
import numpy as np
import mesa
from agent import BDIAgent,Commuter
from shapely.geometry import Point,MultiPoint,Polygon
import random
from collections import Counter
from .building import Floor

class Project(mg.GeoAgent):
    def __init__(self, unique_id, model, building,config, crs=None, render=True):
        if not crs:
            crs = model.space.crs
        self.config = config
        self.building = building
        self.geometry = building.geometry
        self.developer = None
        self.render = render 
        for floor in self.building.floors:
            floor.is_project = True
        super().__init__(unique_id, model, self.geometry , crs)

    def build(self, category, num=1):
        for i in range(num):
            self.new_floor += 1
            self.potential = self.max_new_floor-self.new_floor
            self.building.add_floor(category=category)
    
    def get_residents(self):
        pass

    def cal_demand_list(self):
        pass

    def cal_profit(self):
        pass

    def step(self):
        pass
