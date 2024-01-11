import mesa_geo as mg

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