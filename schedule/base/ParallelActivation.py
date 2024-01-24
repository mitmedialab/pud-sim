from mesa.time import BaseScheduler,RandomActivationByType
from mesa import Agent
from concurrent.futures import ThreadPoolExecutor

class ParallelActivation(BaseScheduler):

    def do_single(self,method, agent_key):
        getattr(self._agents[agent_key], method)()
        return "done"
    
    def parallel_do_each(self, method, agent_keys=None, shuffle=False):
        if agent_keys is None:
            agent_keys = self.get_agent_keys()
        if shuffle:
            self.model.random.shuffle(agent_keys)

        with ThreadPoolExecutor() as executor:
            # Create a list of futures for the executor tasks
            futures = [executor.submit(self.do_single, method, agent_key) for agent_key in agent_keys]
    
    def step(self):
        self.parallel_do_each('parallel_step')
        self.do_each('step')
        self.steps += 1
        self.time += 1


class ParallelActivationByType(RandomActivationByType):

    def do_single(self,method, agent_key):
        getattr(self._agents[agent_key], method)()
        return "done"
    
    def parallel_do_each(self, method, agent_keys=None, shuffle=False):
        if agent_keys is None:
            agent_keys = self.get_agent_keys()
        if shuffle:
            self.model.random.shuffle(agent_keys)

        with ThreadPoolExecutor() as executor:
            # Create a list of futures for the executor tasks
            futures = [executor.submit(self.do_single, method, agent_key) for agent_key in agent_keys]
    
    def step(self,shuffle=False):
        self.parallel_do_each('parallel_step',shuffle=shuffle)
        self.do_each('step',shuffle=shuffle)
        self.steps += 1
        self.time += 1
    
    def step_type(self, type_class,shuffle=False):
        agent_keys: list[int] = list(self.agents_by_type[type_class].keys())
        self.parallel_do_each('parallel_step',agent_keys=agent_keys,shuffle=shuffle)
        self.do_each('step',agent_keys=agent_keys,shuffle=shuffle)
    
    def step_count(self):
        self.steps += 1
        self.time += 1