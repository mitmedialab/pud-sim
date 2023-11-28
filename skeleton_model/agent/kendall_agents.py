import mesa_geo as mg
import numpy as np
import mesa
from agent import BDIAgent,Commuter
from shapely.geometry import Point,MultiPoint,Polygon
import random
from collections import Counter

HEIGHT_PER_FLOOR = 10

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
        self.order_list = {
            "daycare":0,
            "phamacy":1,
            "grocery":2,
            "office_lab":4,
            "family_housing":5,
            "workforce_housing":6,
            "early_career_housing":7,
            "executive_housing":8,
            "senior_housing":9,
        }
        for floor in self.floors:
            self.order_list[floor.Category] = 3
    
    def add_floor(self, floor):
        self.floors.append(floor)
        self.total_floor += 1
        self.reorganize()
    
    def reorganize(self):
        floors = sorted(self.floors, key=lambda x: self.order_list[x.Category])
        for i,floor in enumerate(floors):
            floor.floor = i
            floor.ind = str(self.bld)+"_"+str(floor.floor)
            _coords = [(x, y, HEIGHT_PER_FLOOR*i) for x, y, z in list(floor.geometry.exterior.coords)]
            floor.geometry = Polygon(shell=_coords)

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
        self.height = building.total_floor*12
        self.developer = None
        self.render = render 
        self.new_floor = 0
        self.max_new_floor = random.randint(3,6)
        self.potential = self.max_new_floor-self.new_floor
        for floor in self.building.floors:
            floor.is_project = True

    def add_floor(self, category, num=1):
        for i in range(num):
            self.new_floor += 1
            self.potential = self.max_new_floor-self.new_floor
            geometry = self.building.floors[-1].geometry
            new_floor = Floor(self.model.next_id(), self.model, geometry, render=True)
            new_floor.Category = category
            new_floor.bld = self.bld
            new_floor.area = self.building.floors[-1].area
            new_floor.new = True
            new_floor.is_project = True
            self.building.add_floor(new_floor)
            self.height = self.building.total_floor*HEIGHT_PER_FLOOR
            self.model.space.add_agents([new_floor])

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
        self.set_demand_list()
    
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
        for k,v in self.model.incentive.items():
            self.set_desire(k,np.random.normal(float(v),0.1),-1)
        
    def vote(self):
        desire = self.get_current_desire(by_change=False)
        if desire.intensity > 0.2:
            return desire.key
        else:
            return "No Need"

        
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
        self.expenditure = 0
        self.profit = 0
        self.working_project = None
        
        
    def add_project(self, project):
        self.projects.append(project)
    
    def choose_project(self):
        potential_project = [x for x in self.projects if x.potential > 0]
        if len(potential_project) > 0:
            self.working_project = sorted(potential_project,key=lambda x: x.potential,reverse=True)[0]
        else:
            self.working_project = None
    
    def develope(self):
        if not self.working_project:
            self.choose_project()
            return print("no project")
        elif self.working_project.potential <0:
            self.choose_project()
            return print("no potential")
        else:
            incentive_list = sorted(self.model.incentive.keys(),key=lambda x: self.model.incentive[x],reverse=True)
            category = random.choices(incentive_list[:2], weights=[max(1e-4,self.model.incentive[x]) for x in incentive_list[:2]], k=1)[0]
            if self.model.incentive[category] < 0:
                return print("no incentive")
            else:
                self.working_project.add_floor(category,1)
                self.expenditure -= self.working_project.building.floors[-1].area/10000
                self.profit += (1+self.model.incentive[category])*self.working_project.building.floors[-1].area/10000
                for resident in self.model.residents:
                    desire = resident.get_desire(category)
                    resident.set_desire(category,desire.intensity-0.04,-1)
            
    def step(self):
        self.develope()