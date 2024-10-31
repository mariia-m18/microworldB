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
        self.max_turns = max_turns
        self.visited = set()
        self.frontier = []
        self.position = (0, 0)
        self.exit_found = False
        self.exit_position = None
        self.teleports = {}
        self.agent_a_goals_collected = 0  # Tracks goals collected by Agent A
        self.total_goals_estimate = 0  # Estimate of total goals, updated via messages

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
        turns_left = self.max_turns - self.turn

        """
        match percepts['X'][0]:
            case '0' | '1' | 'r' | 'b':
                return 'U', {'frontier': self.frontier, 'visited': self.visited}
        """
        # Handles incoming messages from Agent A, with focus on exit and teleports
        if msg:
            if msg.get('exit_position') and not self.exit_found:
                self.exit_position = msg['exit_position']  # High priority for exit
                self.exit_found = True
            self.teleports.update(msg.get('teleports', {}))
            self.frontier += msg.get('frontier', [])
            self.visited.update(msg.get('visited', set()))
            # Tracks goals collected by Agent A
            self.agent_a_goals_collected = msg.get('goals_collected', self.agent_a_goals_collected)
            # Updates the total goal estimate if available from Agent A
            self.total_goals_estimate = msg.get('total_goals_estimate', self.total_goals_estimate)

        current_cell = self.position
        self.visited.add(current_cell)

        cell_type = percepts['X'][0]
        self.detect_important_cells(percepts)

        # If exit is reached and Agent A has collected goals or time is short, use the exit
        if cell_type == 'r' and (self.agent_a_goals_collected >= self.total_goals_estimate or turns_left < self.max_turns * 0.2):
            return 'U', self.create_message()

        if cell_type.isdigit() and self.agent_a_goals_collected < self.total_goals_estimate:
            return 'U', self.create_message()

        if cell_type in ('b', 'y', 'o', 'p') and self.should_use_teleport(turns_left):
            return 'U', self.create_message()

        self.update_frontier(percepts)
        print(f"B received the message: {msg}")

        # If exit is known and Agent A’s goals are collected, head directly to the exit
        next_move = self.move_toward(percepts, turns_left) if self.exit_found else self.find_next_move(percepts)

        if next_move:
            self.update_position(next_move)
            return next_move, self.create_message()

        # Random fallback move, prioritizing different directions for diversity
        valid_moves = [d for d in ['E', 'W', 'N', 'S'] if percepts[d][0] != 'w']
        return random.choice(valid_moves) if valid_moves else 'E'

    def detect_important_cells(self, percepts):
        # Focuses only on detecting teleports and exit
        for direction, data in percepts.items():
            if data[0] == 'r' and not self.exit_found:
                self.exit_found = True
                self.exit_position = self.get_new_position(direction)
            elif data[0] in ('b', 'y', 'o', 'p'):  # Found teleport
                self.teleports[data[0]] = self.get_new_position(direction)

    def update_frontier(self, percepts):

        # Direction changes as changes in row and column indices
        directions = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}

        for key, direction in directions.items():
            # Calculates the row and column of the adjacent cell in each direction
            row = self.position[0] + direction[0]
            col = self.position[1] + direction[1]

            # Checks if the cell is not a wall and hasn't been visited
            if percepts[key][0] != 'w' and (row, col) not in self.visited:
                # If the cell is not already in the frontier, adds it to the list
                if (row, col) not in self.frontier:
                    self.frontier.append((row, col))

    def create_message(self):
        return {
            'frontier': [cell for cell in self.frontier if cell not in self.visited],
            'visited': self.visited,
            'exit_position': self.exit_position,
            'teleports': self.teleports,
            'goals_collected': self.agent_a_goals_collected,  # Informs Agent A of goals collected
            'total_goals_estimate': self.total_goals_estimate,  # Inform Agent A of the goal estimate
        }

    def should_use_teleport(self, turns_left):
        return turns_left < self.max_turns * 0.3 or len(self.frontier) > 10

    def find_next_move(self, percepts):

        # Removes any already-visited cells from the frontier
        self.frontier = [cell for cell in self.frontier if cell not in self.visited]

        if self.frontier:
            # Uses A* search to find path to nearest frontier
            direction = self.a_star_search(self.position, self.frontier)
            if direction:
                return direction

        # Default random move if A* fails, prioritezes east west exploration
        valid_moves = [d for d in ['E', 'W', 'N', 'S'] if percepts[d][0] != 'w']
        return random.choice(valid_moves) if valid_moves else 'E'

    def move_toward(self, percepts, turns_left):
        if self.exit_found and turns_left < self.max_turns * 0.2:
            return self.a_star_search(self.position, [self.exit_position])
        elif self.frontier:
            return self.find_next_move(percepts)
        return None

    def a_star_search(self, start, frontier):

        # Priority queue that keeps track of cells to explore, ordered by their priority 
        open_set = []
        heapq.heappush(open_set, (0, start))
        # Dictionary that maps each cell to the cell from which it was reached
        previous_location = {start: None}
        # Dictionary that stores the total cost to reach each cell from the starting cell
        cost_so_far = {start: 0}

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

    def manhattan_distance(self, cell, target_positions):
        # Calculates the number of steps needed to reach one cell from another
        # then returns the smallest distance among the calculated distances to all cells
        return min(abs(cell[0] - target[0]) + abs(cell[1] - target[1]) for target in target_positions)

    def update_position(self, move):
        movement = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
        if move in movement:
            self.position = (self.position[0] + movement[move][0], self.position[1] + movement[move][1])

    def get_new_position(self, move):
        movement = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
        if move in movement:
            return self.position[0] + movement[move][0], self.position[1] + movement[move][1]
        return self.position