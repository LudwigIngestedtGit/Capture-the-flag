"""
This file contains function and classes for the Artificial Intelligence used in the game.
"""
# TODO Fixa så att AI rör på sig om spelaren står still
# TODO Använd previous path för att spara shortest om AI:n resetar. Om den sedan resetar igen ska den försöka hitta en path som är annorlunda

import math
from collections import defaultdict, deque

import pymunk
from pymunk import Vec2d
import gameobjects
import copy

# Constants
MIN_ANGLE_DIF = math.radians(3)   # 3 degrees, a bit more than we can turn each tick


def angle_between_vectors(vec1, vec2):
    """
    Since Vec2d operates in a cartesian coordinate space we have to
    convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2
    vec = vec.perpendicular()
    return vec.angle


def periodic_difference_of_angles(angle1, angle2):
    """
    Compute the difference between two angles.
    """
    return (angle1 % (2 * math.pi)) - (angle2 % (2 * math.pi))


class Ai:
    """
    A simple ai that finds the shortest path to the target using
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes.
    """

    def __init__(self, tank, game_objects_list, tanks_list, space, currentmap):
        self.tank = tank
        self.game_objects_list = game_objects_list
        self.tanks_list = tanks_list
        self.space = space
        self.currentmap = currentmap
        self.flag = None
        self.max_x = currentmap.width - 1
        self.max_y = currentmap.height - 1
        self.forced_reset = False

        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()
        self.bullet_tick = 50
        self.has_fired = False
        self.target_tile = None
        self.shortest_path = None
        self.previous_path = None
        self.other_path = False

    def reveal_position(self, start):
        """
        TEMP: Måste användas till att reveala flaggans position till ai för att de ska använda shortest_path på positionen
        Hitta också tankens start position genom flag och dra shortest på den
        """
        shortest = self.find_shortest_path(target=self.get_tile_of_position(position_vector=start.int_tuple), second_try=False)
        if len(shortest) == 0:
            shortest = self.find_shortest_path(target=self.get_tile_of_position(position_vector=start.int_tuple), second_try=True)
        return shortest

    def update_grid_pos(self):
        """
        This should only be called in the beginning, or at the end of a move_cycle.
        """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)

    def decide(self):
        """
        Main decision function that gets called on every tick of the game.
        """
        self.maybe_shoot()
        next(self.move_cycle)

    def maybe_shoot(self):
        """
        Makes a raycast query in front of the tank. If another tank
        or a wooden box is found, then we shoot.
        """
        # Cooldown for bullet
        if (self.bullet_tick != 50):
            self.bullet_tick += 1
        else:
            angle = self.tank.body.angle + (math.pi / 2)
            offset = 1
            start = (self.tank.body.position[0] + offset * math.cos(angle), self.tank.body.position[1] + offset * math.sin(angle))
            end = (self.tank.body.position[0] + self.currentmap.width * math.cos(angle), self.tank.body.position[1] + self.currentmap.width * math.sin(angle))
            radius = 0
            query_res = self.space.segment_query_first(start, end, radius, pymunk.ShapeFilter())
            if hasattr(query_res, "shape"):
                if hasattr(query_res.shape, "parent"):
                    if isinstance(query_res.shape.parent, gameobjects.Tank) or ((isinstance(query_res.shape.parent, gameobjects.Box) and query_res.shape.parent.destructable)):
                        self.bullet_tick = 0
                        self.has_fired = True

    def switch(self, original_path):
        if self.previous_path == original_path:
            if not self.other_path:
                self.other_path = True
            else:
                self.other_path = False
        self.previous_path = original_path

    def move_cycle_gen(self):
        """
        A generator that iteratively goes through all the required steps
        to move to our goal.
        """
        reset = 0
        while True:
            self.shortest_path = self.find_shortest_path()                                      # Prepare shortest path
            if len(self.shortest_path) == 0:
                self.shortest_path = self.find_shortest_path(target=None, second_try=True)      # Finds path through metal boxes
            if self.other_path:
                self.shortest_path = self.find_shortest_path(target=None)                       # Finds path excluding shortest_path
            if len(self.shortest_path) == 0:
                self.shortest_path = self.find_shortest_path(target=None, second_try=True)      # Finds path through metal boxes when other_path is True
            original_path = copy.copy(self.shortest_path)

            try:
                self.shortest_path.popleft()
            except IndexError:
                continue
            if not self.shortest_path:
                yield
                continue
            next_coord = self.shortest_path.popleft()
            yield

            self.turn(next_coord)
            while not self.correct_angle(next_coord):           # Turn
                reset += 1
                yield
                if self.forced_reset:
                    break
                if reset > 250:
                    self.switch(original_path)
                    break
            self.tank.stop_turning()
            if len(self.shortest_path) >= 1 or self.target_tile is None or self.tank.flag is not None:          # Kör framåt om self.shortest inte har ett element kvar
                self.accelerate()
            while not self.correct_pos(next_coord):             # Drive forward
                reset += 1
                yield
                if self.forced_reset:
                    break
                if reset > 250:
                    self.switch(original_path)
                    break
            self.tank.stop_turning()
            self.tank.stop_moving()
            self.update_grid_pos()
            self.forced_reset = False
            reset = 0

    def find_shortest_path(self, target=None, second_try=False):
        """
        A simple Breadth First Search using integer coordinates as our nodes.
        Edges are calculated as we go, using an external function.
        """
        def save(deq: deque, node):
            deq.append(node)
            return deq

        shortest_path = []
        queue = deque()
        visited_nodes = set()

        if target is None:
            queue.append((self.grid_pos, deque()))
            visited_nodes.add(self.grid_pos.int_tuple)
        else:
            queue.append((self.get_tile_of_position(self.tank.body.position), deque()))
            visited_nodes.add(self.get_tile_of_position(self.tank.body.position).int_tuple)

        while not len(queue) == 0:
            current_node, path = queue.popleft()
            temp = path
            if target is None:
                target = self.get_target_tile()
            if (current_node == target):            # Stanna om man hittar flaggan
                deq = save(copy.deepcopy(temp), current_node)
                for coord in deq:
                    shortest_path.append(coord)
                break
            for neighbor in self.get_tile_neighbors(coord_vec=current_node.int_tuple, second_try=second_try):           # Går igenom alla grannar
                if neighbor not in visited_nodes:
                    deq = save(copy.deepcopy(temp), current_node)
                    queue.append((neighbor, deq))
                    visited_nodes.add(neighbor.int_tuple)
        return deque(shortest_path)

    def get_target_tile(self):
        """
        Returns position of the flag if we don't have it. If we do have the flag,
        return the position of our home base.
        """
        if self.tank.flag is not None:
            x, y = self.tank.start_position
        elif self.target_tile is not None:          # If another tank has picked up the flag
            closest = None
            for cord in self.target_tile:           # Do shortest path for every Vec2d in target tank path
                close = self.find_shortest_path(target=cord, second_try=True)
                if closest is None:
                    closest = close
                elif len(closest) > len(close):     # Save the path to the closest point in target tank path
                    closest = close

                if cord == self.get_tile_of_position(self.grid_pos):        # Stop if we are on the path
                    return self.target_tile[0]
            else:
                if len(closest) >= 1:               # Stops when we arrived at point
                    return closest[-1]
                else:
                    return self.target_tile[0]
        else:
            self.get_flag()         # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """
        This has to be called to get the flag, since we don't know
        where it is when the Ai object is initialized.
        """
        if self.flag is None:
            # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        return self.flag

    def get_tile_of_position(self, position_vector):
        """
        Converts and returns the float position of our tank to an integer position.
        """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec: Vec2d, second_try=False):
        """
        Returns all bordering grid squares of the input coordinate.
        A bordering square is only considered accessible if it is grass
        or a wooden box.
        """
        neighbors = [self.get_tile_of_position(coord_vec) + neighbour for neighbour in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
        if second_try:
            return filter(self.filter_tile_neighbors_second, neighbors)
        elif self.other_path:
            return filter(self.filter_tile_neighbors_second_path, neighbors)
        else:
            return filter(self.filter_tile_neighbors, neighbors)

    def filter_tile_neighbors(self, coord):
        """
        Used to filter the tile to check if it is a neighbor of the tank.
        """
        return (0 <= coord[0] <= self.max_x) and (0 <= coord[1] <= self.max_y) and (self.currentmap.boxAt(coord[0], coord[1]) == 0 or self.currentmap.boxAt(coord[0], coord[1]) == 2)

    def filter_tile_neighbors_second(self, coord):
        """
        Used to filter the tile to check if it is a neighbor of the tank. Metal boxes included.
        """
        return (0 <= coord[0] <= self.max_x) and (0 <= coord[1] <= self.max_y) and (self.currentmap.boxAt(coord[0], coord[1]) == 0 or self.currentmap.boxAt(coord[0], coord[1]) == 2 or self.currentmap.boxAt(coord[0], coord[1]) == 3)

    def filter_tile_neighbors_second_path(self, coord):
        """
        Used to filter the tile to check if it is a neighbor of the tank. Metal boxes included and if the tile is in shortest_path.
        """
        # Check if coord is in shortest path
        filter_path = True
        for elem in range(len(self.previous_path) - 1):
            if coord == self.previous_path[elem]:
                filter_path = False
        # Return cord if it filter_tile_neighbors_second is true and tile not in shortest_path
        return self.filter_tile_neighbors_second(coord) and filter_path

    def turn(self, coord):
        """
        Takes given target coordinate and causes AI tank to turn towards it
        """
        self_angle = self.tank.body.angle
        self_vector = self.tank.body.position
        target_angle = angle_between_vectors(self_vector, coord + (0.5, 0.5))

        if (target_angle - self_angle) % (math.pi * 2) < math.pi:
            self.tank.turn_right()
        else:
            self.tank.turn_left()

    def correct_angle(self, target_coords):
        """
        Checks if tank object is within MIN_ANGLE_DIF parameter relative to a coordinate
        """
        self_angle = self.tank.body.angle
        self_vector = self.tank.body.position
        target_angle = angle_between_vectors(self_vector, target_coords + (0.5, 0.5))
        target_turn_distance = periodic_difference_of_angles(self_angle, target_angle)
        if -1 * MIN_ANGLE_DIF <= target_turn_distance <= MIN_ANGLE_DIF:
            return True
        else:
            return False

    def accelerate(self):
        """
        Causes AI tank to accelerate
        """
        self.tank.accelerate()

    def correct_pos(self, target_coords):
        """
        Checks if tank object has arrived at target coordinates
        """
        euclidean_distance = self.tank.body.position.get_distance(target_coords + (0.5, 0.5))
        if euclidean_distance < 0.1:
            return True
        else:
            return False
