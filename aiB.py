# NAME(S): Mariia Maksymenko, Caleb Thurston
# We wish to have the same grade for this project!
# APPROACH:
# Our goals for both Agents A and B were efficient exploration and goal collection,
# staying in the maze for a reasonable amount of time (until 20-30% of the max turns are left),
# efficient exit search, avoiding teleport loops, efficient communication between agents,
# and finally avoiding visiting the same cells repeteadly. Our Agent A was primarily 
# responsible for collecting goals, and ultimately navigating towards the exit once all known 
# goals were collected or the turn limit was approaching, or also if it knew the exit was really
# far from it. Both agents maintained a frontier set together, which represented cells that were seen but 
# not yet visited. Both of them also used a sort of A* pathfinding algorithm to navigate towards the 
# nearest frontier cell or the exit when necessary, and only move randomly if absolutely necessary.
# Agent A kept track of seen goals and collected goals. If it stepped on a goal cell, it would collect
# it immediately. It was also used to communicate to B how many goals are in an area, and whether they 
# should keep exploring it together, or move on. Both agents have a teleport cooldown mechanism to 
# avoid getting stuck in teleport loops, making it so a minimum number of turns passed before reusing 
# the same teleport pair. To avoid oscillations between adjacent cells or loops in general, both agents 
# stored their recent moves and we tried to make it so they avoid repeating the same movement pattern, 
# but it wasn't succesful, and we aren't sure why. Agent B's role was focusing more on navigating towards 
# the exit while supporting exploration by notifying A of goals when possible. When the exit is located, 
# Agent B would wait in the vicinity or head towards it while keeping track of Agent A's progress in goal 
# collection. Agent B is supposed to ignore whether A collected all the goals if there are little turns left,
# so at least one of the agents can actually exit and get a score. Agent B differed in the fact that it was 
# encouraged to use teleports way more often, so it can explore more cells and not focus on a single area.
# For data structures, we used a lot of sets, as they offer the benfit of being unable to store duplicates,
# and also some dictionaries, so we can make pairs of teleports, coordinates, cell types, etc. As for our
# implememntation of A*, we implemented a priority queue using Python's heapq that keeps track of cells to 
# explore, ordered by their priority. The priority was calculated by combining the path cost so far and the 
# heuristic estimate to the goal. We had a dictionary which tracks each cell and its parent node, and is used 
# to reconstruct the final path once the goal is reached. The agents use Manhattan distance as the heuristic
# because of the restriction of movement to the horizontal and vertical directions. Overall I believe we have
# a good foundation for this project, but we encountered bugs that we weren't sure how to fix, and I do think
# we tried to overfit it to some maps as was mentioned in class.


import random
import heapq

class AI:
    def __init__(self, max_turns):
        self.turn = -1
        self.max_turns = max_turns
        self.visited = set()
        self.frontier = set()
        self.position = (0, 0)
        self.exit_found = False
        self.exit_position = None
        self.teleports = {}
        self.seen_goals = set()  # Set to track all seen goals
        self.collected_goals = set()  # Set to track collected goals
        self.last_teleport_used = None
        self.last_teleport_timer = 0  # Tracks the turns since the last teleport use
        self.teleport_cooldown = 3  # Number of turns before allowing reuse of the last teleport
        self.teleport_pairs = {'o': 'b', 'b': 'o', 'y': 'p', 'p': 'y'}
        self.recent_moves = []

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
        self.last_teleport_timer += 1
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
            self.frontier.update(set(msg.get('frontier', [])))
            self.visited.update(set(msg.get('visited', [])))
            # Adds new seen goals from Agent A's message
            self.seen_goals.update(set(msg.get('new_goals', [])))
            # Adds collected goals from Agent A
            self.collected_goals.update(set(msg.get('collected_goals', [])))

        current_cell = self.position
        self.visited.add(current_cell)
        self.frontier.discard(current_cell)

        cell_type = percepts['X'][0]
        self.detect_important_cells(percepts)

        # If exit is reached and Agent A has collected goals or time is short, uses the exit
        if cell_type == 'r' and (len(self.collected_goals) >= len(self.seen_goals) or turns_left < self.max_turns * 0.2):
            return 'U', self.create_message()

        if cell_type.isdigit() and current_cell not in self.collected_goals:
            return 'U', self.create_message()

        if cell_type in ('b', 'y', 'o', 'p') and self.should_use_teleport(turns_left, cell_type):
            self.last_teleport_used = cell_type
            self.last_teleport_timer = 0  # Resets timer on teleport use
            return 'U', self.create_message()

        self.update_frontier(percepts)
        print(f"B received the message: {msg}")

        # Heads directly to the exit if it’s known and all goals are collected by Agent A
        if self.exit_found:
            if len(self.collected_goals) >= len(self.seen_goals) or turns_left < self.max_turns * 0.3:
                next_move = self.move_toward(percepts)
            else:
                # Waits around the exit if goals are not yet collected
                next_move = self.find_next_move(percepts)
        else:
            # Continues exploring to find the exit
            next_move = self.find_next_move(percepts)

        if next_move and self.is_valid_move(next_move, percepts):
            self.update_position(next_move)
            return next_move, self.create_message()

        valid_moves = [d for d in ['E', 'W', 'N', 'S'] if percepts[d][0] != 'w' and self.get_new_position(d) not in self.recent_moves]
        if valid_moves:
            next_move = random.choice(valid_moves)
            self.update_recent_moves(next_move)
            return next_move, self.create_message()

        # If no valid move that avoids jittering, just picks a move
        next_move = 'E'  # Default move
        self.update_recent_moves(next_move)
        return next_move, self.create_message()


    def detect_important_cells(self, percepts):
        # Focuses only on detecting teleports and exit
        for direction, data in percepts.items():
            new_position = self.get_new_position(direction)
            if data[0] == 'r' and not self.exit_found:
                self.exit_found = True
                self.exit_position = new_position
            elif data[0] in ('b', 'y', 'o', 'p'):  # Found teleport
                self.teleports[data[0]] = new_position
            elif data[0].isdigit() and new_position not in self.seen_goals:
                self.seen_goals.add(new_position)

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
                    self.frontier.add((row, col))

    def create_message(self):
        return {
            'frontier': self.frontier - self.visited,
            'visited': self.visited,
            'exit_position': self.exit_position,
            'teleports': self.teleports,
            'new_goals': self.seen_goals - self.collected_goals,
            'collected_goals': self.collected_goals,
        }

    def should_use_teleport(self, turns_left, teleport_type):
        # Avoids reusing the last teleport pair immediately to prevent teleport loops
        # but allows reuse if enough turns have passed since last use
        last_paired_teleport = self.teleport_pairs.get(self.last_teleport_used)
        return (teleport_type != self.last_teleport_used or self.last_teleport_timer >= self.teleport_cooldown) and teleport_type != last_paired_teleport and ((len(self.frontier) < 20) or turns_left < self.max_turns * 0.7)

    def find_next_move(self, percepts):

        # Removes any already-visited cells from the frontier
        self.frontier -= self.visited

        if self.frontier:
            # Uses A* search to find path to nearest frontier
            direction = self.a_star_search(self.position, self.frontier)
            if direction:
                return direction

        # Default random move if A* fails, prioritezes east west exploration
        valid_moves = [d for d in ['E', 'W', 'N', 'S'] if percepts[d][0] != 'w']
        return random.choice(valid_moves) if valid_moves else 'E'

    def move_toward(self, percepts):
        if self.exit_found:
            return self.a_star_search(self.position, [self.exit_position])
        return None
        """
        if self.exit_found and turns_left < self.max_turns * 0.2:
            return self.a_star_search(self.position, [self.exit_position])
        elif self.frontier:
            return self.find_next_move(percepts)
        return None
        """

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
    
    def is_valid_move(self, move, percepts):
        return move in percepts and percepts[move][0] != 'w'

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

    def update_recent_moves(self, move):
        new_position = self.get_new_position(move)
        self.recent_moves.append(new_position)
        if len(self.recent_moves) > 4:  # Keeps track of the last 4 moves
            self.recent_moves.pop(0)


    def get_new_position(self, move):
        movement = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
        if move in movement:
            return self.position[0] + movement[move][0], self.position[1] + movement[move][1]
        return self.position