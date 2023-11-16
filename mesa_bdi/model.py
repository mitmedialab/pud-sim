import mesa
from agent import *
import numpy as np
# create model
class Model(mesa.Model):
    def __init__(self, N=10,M=1,O=5,width=10, height=10):
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.golds = self.generate_agent(0,N,Gold)
        self.markets = self.generate_agent(N,M,Market)
        self.miners = self.generate_agent(N+M,O,Miner)
        self.running = True
        self.empty_grid = np.ones((width, height))
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if not self.grid.is_cell_empty((x, y)):
                    agent = self.grid.get_cell_list_contents([(x, y)])[0]
                    if type(agent) is Gold:
                        self.empty_grid[x,y] = 0
    
    def generate_agent(self,start,num,AgentType):
        i = start
        agents = []
        while(i<num+start):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            if (self.grid.is_cell_empty((x,y))):
                agent = AgentType(i, self)
                self.schedule.add(agent)
                self.grid.place_agent(agent, (x, y))
                i=i+1
                agents.append(agent)
        return agents

    def step(self):
            self.schedule.step()
            # collect data

    def run_model(self, n):
        for i in range(n):
            self.step()