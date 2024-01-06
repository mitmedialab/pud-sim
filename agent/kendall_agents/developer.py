from  mesa import Agent
from .project import Project

class Developer(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.project = None
        self.profit = 0

    def choose_project(self):
        if not self.project:
            project_list = [x for x in self.model.agents[Project] if x.status == 'pending']
            if len(project_list):
                project_list = sorted(project_list, key=lambda x: x.expected_profit, reverse=True)
                self.project = project_list[0]
                self.project.status = 'building'
        elif self.project.status == 'built':
            self.profit += self.project.expected_profit
            self.project = None
            
    def parallel_step(self):
        pass

    def step(self):
        self.choose_project()
