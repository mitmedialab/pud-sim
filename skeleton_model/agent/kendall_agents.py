import mesa_geo as mg
import numpy as np
import mesa
from agent import BDIAgent,Commuter
from shapely.geometry import Point,MultiPoint,Polygon
import random

class Floor(mg.GeoAgent):
    def __init__(self, unique_id, model, geometry, crs=None, render=True):
        if not crs:
            crs = model.crs
        super().__init__(unique_id, model, geometry, crs)
        self.render = render
        self.is_project = False
        self.new = False
    def step(self):
        pass

class Building(mesa.Agent):
    def __init__(self, unique_id, model, floors, bld, render=True):
        super().__init__(unique_id, model)
        self.floors = sorted(floors, key=lambda x: x.floor)
        self.bld = bld
        self.Category = self.floors[0].Category
        self.total_floor = len(self.floors)
        self.render = render
    
    def add_floor(self, floor):
        self.floors.append(floor)
        self.total_floor += 1

    def step(self):
        pass

class Project(mg.GeoAgent):
    def __init__(self, unique_id, model, building, geometry, crs=None, render=True):
        if not crs:
            crs = model.crs
        super().__init__(unique_id, model, geometry, crs)

        self.bld = building.bld
        self.building = building
        self.init_floor = building.total_floor
        self.height = self.building.floors[-1].geometry.exterior.coords[0][2] + 3
        self.developer = None
        self.render = render 
        self.new_floor = 0
        self.add_floor("Office", num=random.randint(1,10))

    def add_floor(self, category, num=1):
        for i in range(num):
            self.new_floor += 1
            _coords = [(x, y, self.height+self.new_floor*12) for x, y, z in list(self.geometry.exterior.coords)]
            new_geometry = Polygon(shell=_coords)
            new_floor = Floor(self.model.next_id(), self.model, new_geometry, render=True)
            new_floor.Category = category
            new_floor.floor = self.init_floor + self.new_floor
            new_floor.bld = self.bld
            new_floor.ind = str(self.bld)+"_"+str(new_floor.floor)
            new_floor.area = new_geometry.area
            new_floor.new = True
            self.building.add_floor(new_floor)
            self.model.space.add_agents([new_floor])
        
    def call_for_vote(self):
        pass

    def step(self):
        pass


class Resident(Commuter, BDIAgent):
    def __init__(self, unique_id, model, geometry, crs=None, render=True):
        if not crs:
            crs = model.crs
        Commuter.__init__(self,unique_id, model, geometry, crs)
        BDIAgent.__init__(self,unique_id, model)

        self.house = None
        self.office = None
        self.render = render
        self.status = "office"
        self._elevator_step = 0
    
    def _random_point_in_polygon(self,polygon):
        minx, miny, maxx, maxy = polygon.bounds
        offset = min(maxx-minx,maxy-miny)*0.2
        z = polygon.exterior.coords[0][2]
        while True:
            pnt = Point(np.random.uniform(minx+offset, maxx-offset), np.random.uniform(miny+offset, maxy-offset),z)
            # pnt = Point(np.random.uniform(minx+offset, maxx-offset), np.random.uniform(miny+offset, maxy-offset))
            if polygon.contains(pnt):
                break
        return pnt

    
    def set_house(self, house):
        self.house = house
        self.house_point = self._random_point_in_polygon(self.house.geometry)
        self.house_elevator = [(self.house_point.x,self.house_point.y,
                                self.house_point.z-i*self.house_point.z/int(self.house.floor)) 
                                for i in range(int(self.house.floor))]

    def set_office(self, office):
        self.office = office
        self.office_point = self._random_point_in_polygon(self.office.geometry)
        self.geometry = self.office_point
        self.office_elevator = [(self.office_point.x,self.office_point.y,
                                 self.office_point.z-i*self.office_point.z/int(self.office.floor))
                                 for i in range(int(self.office.floor))]
 
        
    def prepare_to_move(self):
        if self.status == "office":
            self.origin = (self.office_point.x,self.office_point.y)
            self.destination = (self.house_point.x,self.house_point.y)
            self._prepare_to_move(self.origin,self.destination)
            self.my_path = [(x,y,0) for (x,y) in self.my_path]
            self.my_path = self.office_elevator[1:] + self.my_path + list(reversed(self.house_elevator)) 
            self.status = "transport"

        if self.status == "house":
            self.origin = (self.house_point.x,self.house_point.y)
            self.destination = (self.office_point.x,self.office_point.y)
            self._prepare_to_move(self.origin,self.destination)
            self.my_path = [(x,y,0) for (x,y) in self.my_path]
            self.my_path = self.house_elevator[1:] + self.my_path + list(reversed(self.office_elevator))
            self.status = "transport"

    def move(self):
        if self.status == "transport":
            self._move()
            if self.geometry == self.house_point:
                self.status = "house"
            if self.geometry == self.office_point:
                self.status = "office"

    def set_demand_list(self):
        self.set_desire("need_transport", 1, -1)

    def vote(self):
        pass

        
    def parallel_step(self):
        # self.prepare_to_move()
        # self.move()
        # print(self.status,self.geometry)
        pass
        
        
    def step(self):
        pass
        

class Developer(BDIAgent):
    def __init__(self, unique_id, model, render=True):
        BDIAgent.__init__(self, unique_id, model)
        self.projects = []
        self.render = render

    def add_project(self, project):
        self.projects.append(project)
        
    def step(self):
        pass