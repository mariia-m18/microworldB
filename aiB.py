# NAME(S): [PLACE YOUR NAME(S) HERE]
#
# APPROACH: [WRITE AN OVERVIEW OF YOUR APPROACH HERE.]
#     Please use multiple lines (< ~80-100 char) for you approach write-up.
#     Keep it readable. In other words, don't write
#     the whole damned thing on one super long line.
#
#     In-code comments DO NOT count as a description of
#     of your approach.

import random
import heapq

class AI:
    def __init__(self, max_turns):
        self.turn = -1
        self.visited = set() # Tracks visited cells
        self.frontier = [] # Frontier of seen but not yet explored cells
        self.position = (0,0) # Initializes starting position
        self.goal_found = False

    def update(self, percepts, msg):
        """
        PERCEPTS:
        Called each turn. Parameter "percepts" is a dictionary containing
        nine entries with the following keys: X, N, NE, E, SE, S, SW, W, NW.
        Each entry's value is a single character giving the contents of the
        map cell in that direction. X gives the contents of the cell the agent
        is in.

        COMAMND:
        This function must return one of the following commands as a string:
        N, E, S, W, U

        N moves the agent north on the map (i.e. up)
        E moves the agent east
        S moves the agent south
        W moves the agent west
        U uses/activates the contents of the cell if it is useable. For
        example, stairs (o, b, y, p) will not move the agent automatically
        to the corresponding hex. The agent must 'U' the cell once in it
        to be transported.

        The same goes for goal hexes (0, 1, 2, 3, 4, 5, 6, 7, 8, 9).
        """
        self.turn += 1

        match percepts['X'][0]:
            case '0' | '1' | 'r' | 'b':
                return 'U', {'frontier': self.frontier, 'visited': self.visited}

        current_cell = self.position
        cell_type = percepts['X'][0]

        if msg:
            self.frontier = list(set(self.frontier + msg.get('frontier', [])))
            self.visited = self.visited.union(msg.get('visited', set()))

        self.visited.add(current_cell)
        self.update_frontier(percepts)

        # If at a goal cell, attempts to use it
        if cell_type.isdigit() and not self.goal_found:
            self.goal_found = True
            return ('U', {'frontier': self.frontier, 'visited': self.visited})
        
        next_move = self.find_next_move(percepts)

        print(f"B received the message: {msg}")
   
        if next_move:
            return (next_move, {'frontier': self.frontier, 'visited': self.visited})

        return random.choice(['N', 'S', 'E', 'W']), "B moving"
    
    def update_frontier(self, percepts):

        # Direction changes as changes in row and column indices
        directions = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}

        for key, direction in directions.items():
            # Calculates the row and column of the adjacent cell in each direction
            row = self.position[0] + direction[0]
            col = self.position[1] + direction[1]

            # Checks if the cell is not a wall and hasn't been visited
            if percepts[key][0] not in ('w',) and (row, col) not in self.visited:
                # If the cell is not already in the frontier, adds it to the list
                if (row, col) not in self.frontier:
                    self.frontier.append((row, col))

    def find_next_move(self, percepts):

        if not self.frontier:
            return 'E'  # Agent B defaults to East for diversity of moves

        nearest_frontier = self.a_star_search(self.position, self.frontier)

        if nearest_frontier:
            return nearest_frontier

        return 'E'
    
    def a_star_search(self, start, frontier):

        # Priority queue that keeps track of cells to explore, ordered by their priority 
        open_set = []
        heapq.heappush(open_set, (0, start))
        # Dictionary that maps each cell to the cell from which it was reached
        previous_location = {start: None}
        # Dictionary that stores the total cost to reach each cell from the starting cell
        cost_so_far = {start: None}

        # While there are nodes to explore
        while open_set:

            # Removes the cell with the lowest priority from queue, setting it as the current cell
            _, current = heapq.heappop(open_set)

            # If we reach a frontier cell
            if current in frontier:
                return self.reconstruct_path(previous_location, current)

            # Iterates over each of the four neighboring cells 
            for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                next_cell = (current[0] + dx, current[1] + dy)
                # Every move just costs 1, so new_cost is the cost to reach current cell plus 1
                new_cost = cost_so_far[current] + 1

                # Checks if next cell hasn't been reached before or if the new path has a lower cost
                if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                    # Updates the cost and priority and adds the new cell to the priority queue
                    cost_so_far[next_cell] = new_cost
                    priority = new_cost + self.manhattan_distance(next_cell, frontier)
                    heapq.heappush(open_set, (priority, next_cell))
                    previous_location[next_cell] = current

        return None  # No path was found
    
    # Backtracks to find the first step that the agent should take toward the target (frontier) cell
    def reconstruct_path(self, previous_location, current):

        # List that stores the cells in reverse order as the method backtracks from the current cell to the start
        path = []
        # Traces each cell’s previous location link
        while current in previous_location and previous_location[current] is not None:
            path.append(current)
            current = previous_location[current]

        # Returns the direction of the next step
        if path:
            next_step = path[-1]
            if next_step[0] < self.position[0]: return 'N'
            if next_step[0] > self.position[0]: return 'S'
            if next_step[1] < self.position[1]: return 'W'
            if next_step[1] > self.position[1]: return 'E'
        
        return 'E'  # Different default direction for Agent B

    def manhattan_distance(self, cell, frontier):
        # Calculates the number of steps needed to reach one cell from another
        # then returns the smallest distance among the calculated distances to all cells
        return min(abs(cell[0] - f[0]) + abs(cell[1] - f[1]) for f in frontier)
            
