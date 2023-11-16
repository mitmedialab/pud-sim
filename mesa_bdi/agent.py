import mesa
from mesa import Agent
from utils import BDIAgent,WalkAgent
import random

class Gold(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.amount = random.randint(1,5)

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
        self.init_behaviors()
    
    # Define agent behaviors
    def init_behaviors(self):

        def find_gold():
            self.wander()

        def get_gold():
            self.target = self.closest_target(self.mine_list,self.model.empty_grid)
            if self.pos == self.target.pos:
                self.gold += 1
                self.target.amount -= 1
                if self.target.amount <= 0:
                    self.model.empty_grid[self.target.pos] = 1

        def sell_gold():
            self.target = self.closest_target(self.model.markets,self.model.empty_grid)
            if self.pos == self.target.pos:
                if self.gold > 0:
                    self.gold -= 1 
                    self.money += 1
                    self.remove_desire('sell_gold')
        
        self.set_intension('find_gold',find_gold)
        self.set_intension('get_gold',get_gold)
        self.set_intension('sell_gold',sell_gold)
    
    # How agents observe the environment and generate beliefs
    def observe(self,moore=True,radius=1):
        neighbors = self.model.grid.get_neighbors(self.pos,moore=moore,radius=radius)
        for n in neighbors:
            if type(n) is Gold:
                if n.amount > 0 and n not in self.mine_list:
                    self.mine_list.append(n)
                    self.set_belief('has_gold',self.mine_list)
                if n.amount <= 0 and n in self.mine_list:
                    self.mine_list.remove(n)
                    self.set_belief('has_gold',self.mine_list)

    # How agents generate desires according to their beliefs
    def think(self):
        # 'find_gold' desire rules
        if len(self.mine_list) <= 0:
            self.set_desire('find_gold',3,-1)
        if self.money <= 0:
            self.set_desire('find_gold',1,-1)
        if self.money >1:
            self.remove_desire('find_gold')
        # 'get_gold' desire rules
        if len(self.mine_list) > 0:
            self.set_desire('get_gold',2,-1)
        if len(self.mine_list) <= 0 and 'get_gold' in self.desire_base.keys():
            self.remove_desire('get_gold')
        if self.gold > 1:
            self.remove_desire('get_gold')
        # 'sell_gold' desire rules
        if self.gold > 0:
            self.set_desire('sell_gold',3,-1)
    
    def act(self):
        # get current intension and act
        intension = self.get_current_intension(by_change=False)
        if intension is not None:
            intension.act()

    def step(self):
        self.observe()
        self.think()
        self.act()
        print(self.get_current_desire(by_change=False))
        if self.target:
            self.move(self.target,self.model.empty_grid)
            if self.pos == self.target.pos:
                self.target=None
        else:
            self.wander()