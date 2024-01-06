import mesa_geo as mg
from shapely.geometry import Polygon
from collections import defaultdict
from .resident import Resident
from .project import Project
from .floor import Floor

class Building(mg.GeoAgent):
    def __init__(self, unique_id, model, floors, bld, config, crs=None,render=True):
        if not crs:
            crs = model.space.crs
        self.floors = floors
        self.bld = bld
        self.render = render
        self.config = config
        self.project = None
        self.reorganize()
        super().__init__(unique_id, model,self.geometry, crs)
    
    def reorganize(self):
        floors = sorted(self.floors, key=lambda x: self.config.order.index(x.Category) if x.Category in self.config.order else 6)
        for i,floor in enumerate(floors):
            floor.floor = i
            floor.ind = str(self.bld)+"_"+str(floor.floor)
            _coords = [(x, y, self.config.height_per_floor*i) for x, y, z in list(floor.geometry.exterior.coords)]
            floor.geometry = Polygon(shell=_coords)
        self.floors = floors
        self.geometry = self.floors[0].geometry.representative_point()
        for floor in self.floors:
            floor.building = self
            if self.project:
                floor.is_project = True
                floor.project = self.project
    
    def get_neighbors(self):
        self.neighbor = defaultdict(list)
        self.neighbor[Building].append(self)
        self.neighbor[Floor].extend(self.floors)
        neighbors = self.model.space.get_neighbors_within_distance(self, self.config.life_circle_radius)
        for neighbor in neighbors:
            if isinstance(neighbor, Building):
                self.neighbor[Building].append(neighbor)
                for floor in neighbor.floors:
                    self.neighbor[Floor].append(floor)
            elif isinstance(neighbor, Resident):
                self.neighbor[Resident].append(neighbor)
            elif isinstance(neighbor, Project):
                self.neighbor[Project].append(neighbor) 
    
    def add_floor(self, category=None, floor=None):
        if floor:
            new_floor = floor
        else:
            geometry = self.floors[-1].geometry
            new_floor = Floor(self.model.next_id(), self.model, geometry, render=True)
            new_floor.Category = category
            new_floor.bld = self.bld
            new_floor.area = self.floors[-1].area
            new_floor.new = True
        new_floor.building = self
        self.floors.append(new_floor)
        self.neighbor[Floor].append(new_floor)
        self.model.agents[Floor].append(new_floor)
        self.model.space.add_agents([new_floor])
        self.reorganize()
        return new_floor

    def step(self):
        pass