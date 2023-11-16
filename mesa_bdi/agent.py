import mesa
from mesa import Agent
from .utils import BDIAgent,WalkAgent
import random

class Gold(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.amount = random.randint(1,100)

    def step(self):
        pass

class Market(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id

    def step(self):
        pass

class Miner(BDIAgent,WalkAgent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.money = 0
        self.gold = 0
        self.mine_list = []
        self.empty_mine_list = []
        for agent in self.model.schedule.agents:
            if type(agent) is Market:
                self.target = agent
    
    def observe(self):
        self.mine_list.append({"location":(0,0),"amount":100})
        self.set_belief('has_gold',self.mine_list)
        self.set_belief('empty_mine',self.empty_mine_list)
        pass

    def plan(self):
        if self.money <= 0:
            self.set_desire('find_gold',1,-1)
        if len(self.mine_list) > 0:
            self.set_desire('get_gold',2,-1)
        if self.gold > 0:
            self.set_desire('sell_gold',3,-1)
        pass
    
    def act(self, desire: str):
        if desire == 'find_gold':
            self.target = random.choice(self.model.schedule.agents)
        if desire == 'get_gold':
            self.target = random.choice(self.mine_list)
        if desire == 'sell_gold':
            self.target = random.choice(self.model.schedule.agents)
        return super().get_current_intension(desire)

    def step(self):
        if self.target:
            self.move(self.target,self.model.empty_grid)
        else:
            self.wander()