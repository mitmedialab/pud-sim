from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement
import mesa
from mesa import Agent

class WalkAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.target = None

    
    def _find_path(self, target, grid):
        grid = Grid(matrix=grid)
        # Set start and end nodes
        # The order of x,y in pathfinder is opposite to that of mesa!!!
        start = grid.node(self.pos[1], self.pos[0])
        end = grid.node(target.pos[1], target.pos[0])

        # Find the path
        finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
        path, _ = finder.find_path(start, end, grid)

        return path

    def wander(self):
        # Pick the next cell from the adjacent cells.
        next_moves = self.model.grid.get_neighborhood(self.pos, True, True)
        next_move = self.random.choice(next_moves)
        # Now move:
        self.model.grid.move_agent(self, next_move)

    def move(self, target, grid):
        path = self._find_path(target, grid)
        # If a path is found, move the agent to the next position
        if len(path)>1:
            next_move = path[1]
            next_move = (next_move.y, next_move.x) 
            self.model.grid.move_agent(self, next_move)
    
    def closest_target(self, target_list, grid):
        min_path_length = 100000
        cloest_target = None
        for target in target_list:
            path = self._find_path(target, grid)
            if len(path) < min_path_length:
                cloest_target = target
        return cloest_target

    def step(self):
        pass