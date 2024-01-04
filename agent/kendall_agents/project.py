import mesa_geo as mg
from .resident import Resident

class Project(mg.GeoAgent):
    def __init__(self, unique_id, model, building,config, crs=None, render=True):
        if not crs:
            crs = model.space.crs
        self.config = config
        self.building = building
        self.geometry = building.geometry
        self.render = render 
        for floor in self.building.floors:
            floor.is_project = True
        super().__init__(unique_id, model, self.geometry , crs)
    
    def get_residents(self):
        neighbors = self.model.space.get_neighbors_within_distance(self, self.config.project_range)
        self.residents = []
        for neighbor in neighbors:
            if isinstance(neighbor, Resident):
                self.residents.append(neighbor)
    
    def cal_max_capacity(self):
        pass

    #sum the demand gap from nearby residents
    def cal_demand_list(self):
        self.demand_list = {}
        for key in self.config.amenity_list:
            if key not in self.demand_list:
                self.demand_list[key] = 0
            for resident in self.residents:
                self.demand_list[key] += resident.weighted_demand_gap[key]
    
    #calculate incentive for different amenities based on demand gap
    def cal_incentive(self):
        self.incentive = {}
        sorted_demand_list = sorted(self.demand_list.keys(), key=lambda k: self.demand_list[k])
        for idx, category in enumerate(sorted_demand_list):
            self.incentive[category] = self.config.incentive_list[idx]

    #calcaulte expected profit of different amenities
    def cal_profit(self):
        self.expected_profit = {}
        for idx, category in enumerate(self.config.amenity_list):
            demand_area = self.demand_list[category]
            reward_area = self.incentive[category]*demand_area
            self.expected_profit[category] = self.config.profit_list[idx]*demand_area + max(self.config.profit_list)*reward_area

    #build floor with maximum expected profit
    def build(self):
        category = max(self.expected_profit, key=self.expected_profit.get)
        floor = self.building.add_floor(category=category)
        for resident in self.residents:
            resident.neighbor_floors.append(floor)
    
    def parallel_step(self):
        pass

    def step(self):
        self.cal_demand_list()
        self.cal_incentive()
        self.cal_profit()
        self.build()
