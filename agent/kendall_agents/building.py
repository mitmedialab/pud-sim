import mesa_geo as mg
from shapely.geometry import Polygon


class Floor(mg.GeoAgent):
    def __init__(self, unique_id, model, geometry, crs=None, render=True):
        if not crs:
            crs = model.space.crs
        super().__init__(unique_id, model, geometry, crs)
        self.render = render
        self.is_project = False
        self.new = False
    def step(self):
        pass

class Building(mg.GeoAgent):
    def __init__(self, unique_id, model, floors, bld, config, crs=None,render=True):
        if not crs:
            crs = model.space.crs
        self.floors = floors
        self.bld = bld
        self.render = render
        self.config = config
        self.reorganize()
        super().__init__(unique_id, model,self.geometry, crs)
    
    def add_floor(self, category=None, floor=None):
        if floor:
            new_floor = floor
            self.floors.append(new_floor)
        else:
            geometry = self.floors[-1].geometry
            new_floor = Floor(self.model.next_id(), self.model, geometry, render=True)
            new_floor.Category = category
            new_floor.bld = self.bld
            new_floor.area = self.floors[-1].area
            new_floor.new = True
            new_floor.is_project = True
            self.floors.append(new_floor)
            self.model.space.add_agents([new_floor])
        self.reorganize()
        return new_floor
    
    def reorganize(self):
        floors = sorted(self.floors, key=lambda x: self.config.order.index(x.Category) if x.Category in self.config.order else 6)
        for i,floor in enumerate(floors):
            floor.floor = i
            floor.ind = str(self.bld)+"_"+str(floor.floor)
            _coords = [(x, y, self.config.height_per_floor*i) for x, y, z in list(floor.geometry.exterior.coords)]
            floor.geometry = Polygon(shell=_coords)
        self.floors = floors
        self.geometry = self.floors[0].geometry.representative_point()

    def step(self):
        pass