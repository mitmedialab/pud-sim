from  mesa import Agent
import random

# define belief
class Belief:
    def __init__(self, key:str, value:object):
        self.key = key
        self.value = value

# define desire
class Desire:
    def __init__(self, key:str, intensity:float, lifetime:int):
        self.key = key
        self.intensity = intensity
        self.lifetime = lifetime
        assert self.lifetime > 0, "lifetime must be greater than 0"

# define intention
class Intension:
    def __init__(self, key:str, action:callable):
        self.key = key
        self.action = action
    def run(self):
        return self.action()

# define BDI agent
class BDIAgent(Agent):
    def __init__(self, unique_id:int, model:object):
        super().__init__(unique_id, model)
        self.belief_base = {}
        self.desire_base = {}
        self.intension_base = {}

    def set_belief(self, key:str, value:object):
        #add or set belief
        self.belief_base[key] = Belief(key, value)
    
    def remove_belief(self, key:str):
        # remove belief if it exists
        if key in self.belief_base:
            del self.belief_base[key]
    
    def set_desire(self, key:str, intensity:float, lifetime:int):
        #add or set desire
        self.desire_base[key] = Desire(key, intensity, lifetime)
    
    def remove_desire(self, key:str):
        # remove desire if it exists
        if key in self.desire_base:
            del self.desire_base[key]

    def update_desire(self):
        # update desire intensity by lifetime
        for key in self.desire_base:
            # if lifetime is miner than 0, the desire is permanent
            if self.desire_base[key].lifetime > 0:
                self.desire_base[key].intensity -= 1/self.desire_base[key].lifetime
            if self.desire_base[key].intensity == 0:
                self.remove_desire(key)

    def set_intension(self, key:str, action:callable):
        #add or set intension
        self.intension_base[key] = Intension(key, action)

    def get_current_desire(self):
        #the desire with the highest intensity is chosen
        desires = [self.desire_base[key] for key in self.desire_base]
        current_desire = max(desires, key=lambda x: x.intensity)
        return current_desire
    
    def get_current_desire_by_chance(self):
        #the chance of choosing a desire is proportional to its intensity
        desires = [self.desire_base[key] for key in self.desire_base]
        current_desire = random.choices(desires, weights=lambda x: x.intensity, k=1)[0]
        return current_desire
    
    def observe(self):
        # the rules of generating belief
        pass
    
    def plan(self):
        # the rules of generating desire
        pass
    
    def act(self,desire:str):
        #the rules of choosing intension by desire
        pass

    def step(self):
        # update each step
        pass