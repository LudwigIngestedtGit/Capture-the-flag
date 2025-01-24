"""
This module contains support for the different game objects: tank, boxes...
"""
import math
import pygame
import pymunk
import images

# All the different objects that have collision
collision_types = {
    "tank": 1,
    "bullet": 2,
    "box": 3,
    "boundry": 4
}

DEBUG = False  # Change this to set it in debug mode
# Global variables
global modifier
modifier = 1


def physics_to_display(x):
    """
    This function is used to convert coordinates in the physic engine into the display coordinates
    """
    return x * images.TILE_SIZE


def degrees_to_radians(degree):
    """
    Changes degrees to radians
    """
    return degree * math.pi / 180


class GameObject:
    """
    Parent class to all objects in the game
    """
    def __init__(self, sprite):
        """
        Sets the sprite of the gameobject. All gameobjects should have a sprite.
        """
        self.sprite = sprite

    def update(self):
        """
        Placeholder, supposed to be implemented in a subclass.
        Should update the current state (after a tick) of the object.
        """
        return

    def post_update(self):
        """
        Should be implemented in a subclass. Make updates that depend on
        other objects than itself.
        """
        return

    def update_screen(self, screen):
        """
        Updates the visual part of the game. Should NOT need to be changed
        by a subclass.
        """
        sprite = self.sprite

        p = self.screen_position()  # Get the position of the object (pygame coordinates)
        sprite = pygame.transform.rotate(sprite, self.screen_orientation())  # Rotate the sprite using the rotation of the object

        # The position of the screen correspond to the center of the object,
        # but the function screen.blit expect to receive the top left corner
        # as argument, so we need to adjust the position p with an offset
        # which is the vector between the center of the sprite and the top left
        # corner of the sprite
        offset = pymunk.Vec2d(*sprite.get_size()) / 2.
        p = p - offset
        screen.blit(sprite, p)  # Copy the sprite on the screen


class GamePhysicsObject(GameObject):
    """
    This class extends GameObject and it is used for objects which have a
    physical shape (such as tanks and boxes). This class handle the physical
    interaction of the objects.
    """

    def __init__(self, x, y, orientation, sprite, space, movable):
        """
        Takes as parameters the starting coordinate (x,y), the orientation, the sprite (aka the image
        representing the object), the physic engine object (space) and whether the object can be
        moved (movable).
        """

        super().__init__(sprite)

        # Half dimensions of the object converted from screen coordinates to physic coordinates
        half_width = 0.5 * self.sprite.get_width() / images.TILE_SIZE
        half_height = 0.5 * self.sprite.get_height() / images.TILE_SIZE

        # Physical objects have a rectangular shape, the points correspond to the corners of that shape.
        points = [[-half_width, -half_height],
                  [-half_width, half_height],
                  [half_width, half_height],
                  [half_width, -half_height]]
        self.points = points

        # Create a body (which is the physical representation of this game object in the physic engine)
        if movable:
            # Create a movable object with some mass and moments
            # (considering the game is a top view game, with no gravity,
            # the mass is set to the same value for all objects)."""
            mass = 10
            moment = pymunk.moment_for_poly(mass, points)
            self.body = pymunk.Body(mass, moment)
        else:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)  # Create a non movable (static) object

        self.body.position = x, y
        self.body.angle = math.radians(orientation)       # orientation is provided in degress, but pymunk expects radians.
        self.shape = pymunk.Poly(self.body, points)  # Create a polygon shape using the corner of the rectangle
        self.shape.parent = self

        # Add the object to the physic engine
        space.add(self.body, self.shape)

    def screen_position(self):
        """
        Converts the body's position in the physics engine to screen coordinates.
        """
        return physics_to_display(self.body.position)

    def screen_orientation(self):
        """
        Angles are reversed from the engine to the display.
        """
        return -math.degrees(self.body.angle)

    def update_screen(self, screen):
        """
        Updates screen to match new position of object after interactions
        """
        super().update_screen(screen)
        # debug draw
        if DEBUG:
            ps = [self.body.position + p for p in self.points]

            ps = [physics_to_display(p) for p in ps]
            ps += [ps[0]]
            pygame.draw.lines(screen, pygame.color.THECOLORS["red"], False, ps, 1)


def clamp(min_max, value):
    """
    Convenient helper function to bound a value to a specific interval.
    """
    return min(max(-min_max, value), min_max)


class Tank(GamePhysicsObject):
    """
    Extends GamePhysicsObject and handles aspects which are specific to our tanks.
    """

    # Constant values for the tank, acessed like: Tank.ACCELERATION
    ACCELERATION = 0.4
    NORMAL_MAX_SPEED = 2.0
    FLAG_MAX_SPEED = NORMAL_MAX_SPEED * 0.5

    def __init__(self, x, y, orientation, sprite, space, player_number, difficulty_modifier):
        super().__init__(x, y, orientation, sprite, space, True)
        global modifier
        modifier = difficulty_modifier
        # Define variable used to apply motion to the tanks
        self.acceleration = 0  # 1 forward, 0 for stand still, -1 for backwards
        self.rotation = 0  # 1 clockwise, 0 for no rotation, -1 counter clockwise

        self.flag = None                      # This variable is used to access the flag object, if the current tank is carrying the flag
        self.max_speed = Tank.NORMAL_MAX_SPEED * modifier     # Impose a maximum speed to the tank
        self.start_position = pymunk.Vec2d(x, y)        # Define the start position, which is also the position where the tank has to return with the flag
        self.start_angle = degrees_to_radians(orientation)
        self.shape.collision_type = collision_types["tank"]
        self.circle = []
        self.score = 0
        self.player_number = player_number

    def accelerate(self):
        """
        Call this function to make the tank move forward.
        """
        self.acceleration = modifier

    def stop_moving(self):
        """
        Call this function to make the tank stop moving.
        """
        self.acceleration = 0
        self.body.velocity = pymunk.Vec2d.zero()

    def decelerate(self):
        """
        Call this function to make the tank move backward.
        """
        self.acceleration = -1

    def turn_left(self):
        """
        Makes the tank turn left (counter clock-wise).
        """
        self.rotation = -1

    def turn_right(self):
        """
        Makes the tank turn right (clock-wise).
        """
        self.rotation = 1

    def stop_turning(self):
        """
        Call this function to make the tank stop turning.
        """
        self.rotation = 0
        self.body.angular_velocity = 0

    def update(self):
        """
        A function to update the objects coordinates. Gets called at every tick of the game.
        """

        # Creates a vector in the direction we want accelerate / decelerate
        acceleration_vector = pymunk.Vec2d(0, self.ACCELERATION * self.acceleration).rotated(self.body.angle)
        # Applies the vector to our velocity
        self.body.velocity += acceleration_vector

        # Makes sure that we dont exceed our speed limit
        velocity = clamp(self.max_speed, self.body.velocity.length)
        self.body.velocity = pymunk.Vec2d(velocity, 0).rotated(self.body.velocity.angle)

        # Updates the rotation
        self.body.angular_velocity += self.rotation * self.ACCELERATION
        self.body.angular_velocity = clamp(self.max_speed, self.body.angular_velocity)

    def post_update(self):
        """
        Update function that handles changes from other objects
        """
        # If the tank carries the flag, then update the positon of the flag
        if (self.flag is not None):
            self.flag.x = self.body.position[0]
            self.flag.y = self.body.position[1]
            self.flag.orientation = -math.degrees(self.body.angle)
        # Else ensure that the tank has its normal max speed
        else:
            self.max_speed = Tank.NORMAL_MAX_SPEED

    def try_grab_flag(self, flag):
        """
        Call this function to try to grab the flag, if the flag is not on other tank
        and it is close to the current tank, then the current tank will grab the flag.
        """
        # Check that the flag is not on other tank
        if not flag.is_on_tank:
            # Check if the tank is close to the flag
            flag_pos = pymunk.Vec2d(flag.x, flag.y)
            if (flag_pos - self.body.position).length < 0.7:
                # Grab the flag !
                self.flag = flag
                flag.is_on_tank = True
                flag.tank_start_pos = self.start_position
                self.max_speed = Tank.FLAG_MAX_SPEED

    def has_won(self):
        """
        Check if the current tank has won (if it is has the flag and it is close to its start position).
        """
        return self.flag is not None and (self.start_position - self.body.position).length < 0.2

    def shoot(self, space):
        """
        Call this function to shoot a missile.
        """
        bullet = Bullet(self.body.position[0], self.body.position[1], 0, images.bullet, space, self.body.angle)
        return bullet


class Bullet(GamePhysicsObject):
    """
    Extends GamePhysicsObject and handles aspects which are specific to our bullets.
    """
    global modifier
    MAX_SPEED = 4.0 * modifier

    def __init__(self, x, y, orientation, sprite, space, rotation):
        super().__init__(x, y, orientation, sprite, space, True)
        self.acceleration = 1  # Moving forward
        self.body.angle = rotation
        self.max_speed = Bullet.MAX_SPEED
        self.body.position = pymunk.Vec2d(x, y) + pymunk.Vec2d(1.8 * self.sprite.get_height() / images.TILE_SIZE, 0).rotated(self.body.angle + math.pi / 2)
        self.shape.collision_type = collision_types["bullet"]

    def update(self):
        """
        Updates Bullet object
        """
        self.body.velocity = pymunk.Vec2d(self.max_speed, 0).rotated(self.body.angle + math.pi / 2)
        return


class Box(GamePhysicsObject):
    """
    This class extends the GamePhysicsObject to handle box objects.
    """

    def __init__(self, x, y, sprite, movable, space, destructable):
        """
        It takes as arguments the coordinate of the starting position of the box (x,y) and the box model (boxmodel).
        """
        super().__init__(x, y, 0, sprite, space, movable)
        self.destructable = destructable
        self.shape.collision_type = collision_types["box"]


def get_box_with_type(x, y, type, space):
    """
    Create a box with the correct type at coordinate x, y.
     - type == 1 create a rock box
     - type == 2 create a wood box
     - type == 3 create a metal box
    Other values of type are invalid
    """
    (x, y) = (x + 0.5, y + 0.5)  # Offsets the coordinate to the center of the tile
    if type == 1:  # Creates a non-movable non-destructable rockbox
        return Box(x, y, images.rockbox, False, space, False)
    if type == 2:  # Creates a movable destructable woodbox
        return Box(x, y, images.woodbox, True, space, True)
    if type == 3:  # Creates a movable non-destructable metalbox
        return Box(x, y, images.metalbox, True, space, False)


class GameVisibleObject(GameObject):
    """ This class extends GameObject for object that are visible on screen but have no physical representation (bases and flag) """

    def __init__(self, x, y, sprite):
        """ It takes argument the coordinates (x,y) and the sprite. """
        self.x = x
        self.y = y
        self.orientation = 0
        super().__init__(sprite)

    def screen_position(self):
        """ Overwrite from GameObject """
        return physics_to_display(pymunk.Vec2d(self.x, self.y))

    def screen_orientation(self):
        """ Overwrite from GameObject """
        return self.orientation


class Flag(GameVisibleObject):
    """ This class extends GameVisibleObject for representing flags."""

    def __init__(self, x, y):
        self.is_on_tank = False
        super().__init__(x, y, images.flag)
        self.start_position = (x, y)
        self.tank_start_pos = (x, y)
