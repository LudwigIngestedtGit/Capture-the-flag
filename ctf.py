"""
Main file for the game.
"""
import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
import time
import argparse
import json

# ----- Initialisation ----- #

# -- Initialise the display
pygame.init()
pygame.display.set_mode()

# -- Initialise the clock
clock = pygame.time.Clock()

# -- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0, 0.0)
space.damping = 0.1  # Adds friction to the ground for all objects

# -- Import from the ctf framework
# The framework needs to be imported after initialisation of pygame
import ai
import images
import gameobjects
import maps
import screens

# -- Constants
FRAMERATE = 50

# -- Variables
# List of all game objects
game_objects_list = []
tanks_list = []
ai_list = []


# Creates different command line options
def parse_arguments():
    parser = argparse.ArgumentParser(description='Your Pygame Game')
    parser.add_argument("--map", metavar="", dest="map", help="Allows you to enter map for capture the flag game, default is none", required=False)
    return parser.parse_args()


args = parse_arguments()

json_map = None
# Reads json file map if a file is given
if args.map is not None:
    json_file_name = 'json_maps/' + args.map
    f = open(json_file_name)
    data = json.load(f)

    json_map = maps.Map(data['width'], data['height'], data['boxes'], data['tanks_start'], data['flag_start'])

    # Closing file
    f.close()


# -- Resize the screen to the size of the current level
def resize_screen():
    """
    Sets screen size to map size
    """
    screen = pygame.display.set_mode(current_map.rect().size)
    return screen


# -- Created the fog of war
def fog_of_war(fog_of_war_color):
    """
    Creates the fog of war
    """
    screen_black = pygame.Surface(screen.get_size())
    screen_black.fill(fog_of_war_color)
    return screen_black


# -- Generate the background
def generate_background():
    """
    Generates background tiles for the game
    """
    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            # The blit function will copy the image cointained in image.grass to the
            # coordinates given at the second argument
            background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))


# -- Creates the static lines (Map boundaries)
def create_boundaries():
    """
    Creates static lines in the form of pymunk.Segments that act as map boundaries
    """
    x = current_map.width
    y = current_map.height
    static_body = space.static_body
    static_lines = [
        pymunk.Segment(static_body, (0, 0), (x, 0), 0),
        pymunk.Segment(static_body, (x, 0), (x, y), 0),
        pymunk.Segment(static_body, (x, y), (0, y), 0),
        pymunk.Segment(static_body, (0, y), (0, 0), 0)
    ]
    for line in static_lines:
        line.elasticity = 0
        line.friction = 1
        line.collision_type = gameobjects.collision_types["boundry"]
        space.add(line)


# -- Creates the boxes
def create_boxes():
    """
    Creates box obstacles based on map and adds to list of gameobjects.
    Boxes take positional arguments and type from the maps.py file.
    """
    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            # Get the type of boxes
            box_type = current_map.boxAt(x, y)
            # If the box type is not 0, create a box
            if (box_type != 0):
                # Create a box using the box_type as well as the x, y coordinates
                # and pymunk space
                box = gameobjects.get_box_with_type(x, y, box_type, space)
                game_objects_list.append(box)


# -- Create the tanks and the bases
def create_tanks(selected_difficulty):
    """
    Iterates over list of starting positions from maps.py and creates tanks and bases on the corresponding positions.
    Also creates Ai objects for non-player tanks.
    """
    difficulty_modifier = 1
    if selected_difficulty == "easy":
        difficulty_modifier = 0.7
    elif selected_difficulty == "hard":
        difficulty_modifier = 1.3

    # Loop over starting positions
    for i in range(0, len(current_map.start_positions)):
        # Get the starting position of the tank "i"
        pos = current_map.start_positions[i]
        # Create the tank, images.tanks contains the image of the tank
        if i == 0:
            tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space, i + 1, 1)
        else:
            tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space, i + 1, difficulty_modifier)
        base = gameobjects.GameVisibleObject(pos[0], pos[1], images.bases[i])
        # Adds the tank and base to lists
        tanks_list.append(tank)
        game_objects_list.append(base)
        game_objects_list.append(tank)
        # Adds the AI to tanks
        bot = ai.Ai(tank, game_objects_list, tanks_list, space, current_map)
        ai_list.append(bot)


# -- Create the flag
def create_flag():
    """
    Creates flag object at position given by maps.py.
    """
    flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
    game_objects_list.append(flag)
    return flag


# --Collisions handlers
def create_collision_handlers():
    """
    Creates collision handlers for each type of collision interaction.
    """
    handler_bullet_tank = space.add_collision_handler(gameobjects.collision_types["bullet"], gameobjects.collision_types["tank"])
    handler_bullet_box = space.add_collision_handler(gameobjects.collision_types["bullet"], gameobjects.collision_types["box"])
    handler_bullet_boundry = space.add_collision_handler(gameobjects.collision_types["bullet"], gameobjects.collision_types["boundry"])
    return handler_bullet_box, handler_bullet_tank, handler_bullet_boundry


# Runs the initialization of the game
def initialization(selected_map, selected_difficulty):
    """
    Initializes the game
    """
    # Global variables
    global total_game_time
    global total_round_number
    global screen
    global background
    global flag
    global handler_bullet_box
    global handler_bullet_tank
    global handler_bullet_boundry
    global current_map

    # Sets the map to the selected map
    if args.map is not None:
        if selected_map == "json_map":
            current_map = json_map
    if selected_map == "map0":
        current_map = maps.map0
    elif selected_map == "map1":
        current_map = maps.map1
    elif selected_map == "map2":
        current_map = maps.map2

    # Resets/sets all the variables to their original game launch state
    total_round_number = 0
    total_game_time = 0

    # Runs all the initilazation functions
    screen = resize_screen()
    background = pygame.Surface(screen.get_size())
    generate_background()
    create_boundaries()
    create_boxes()
    create_tanks(selected_difficulty)
    flag = create_flag()
    handler_bullet_box, handler_bullet_tank, handler_bullet_boundry = create_collision_handlers()

    # Starts the game
    return "main"


# ----- Main Loop ----- #
currently_running = "welcome"
exit_game = False


# --Collision for bullet
def collision_bullet_tank(arb, space, data):
    """
    Handles collision between tanks and bullets and removes both.
    """
    # Drops the flag
    if flag.is_on_tank:
        flag.is_on_tank = False
        arb.shapes[1].parent.flag = None

    # Removes bullet
    try:
        game_objects_list.remove(arb.shapes[0].parent)
        space.remove(arb.shapes[0], arb.shapes[0].body)
    except (IndexError, ValueError):
        pass

    # Moves tank to start_position
    arb.shapes[1].parent.body.position = arb.shapes[1].parent.start_position
    arb.shapes[1].parent.body.velocity = pymunk.Vec2d.zero()
    arb.shapes[1].parent.body.angular_velocity = 0
    arb.shapes[1].parent.rotation = 0
    arb.shapes[1].parent.body.angle = arb.shapes[1].parent.start_angle

    # Changes the target of the ai
    for ai in ai_list:
        ai.target_tile = None
        ai.forced_reset = True

    return True


def collision_bullet_box(arb, space, data):
    """
    Handles collision between bullets and boxes, removing bullet and removes box if destructible
    """
    # Remove bullet if bullet exists
    try:
        game_objects_list.remove(arb.shapes[0].parent)
        space.remove(arb.shapes[0], arb.shapes[0].body)
    except (IndexError, ValueError):
        pass
    # Remove box if destructable
    if arb.shapes[1].parent.destructable:
        space.remove(arb.shapes[1], arb.shapes[1].body)
        game_objects_list.remove(arb.shapes[1].parent)
    return True


def collision_bullet_boundry(arb, space, data):
    """
    Handles collision between bullet and map boundry, removing the bullet upon impact.
    """
    # Remove bullet if bullet exists
    try:
        game_objects_list.remove(arb.shapes[0].parent)
        space.remove(arb.shapes[0], arb.shapes[0].body)
    except (IndexError, ValueError):
        pass


def reset_game():
    """
    Resets game
    """
    # Resets all the tanks
    for tank in tanks_list:
        tank.body.position = tank.start_position
        tank.body.velocity = pymunk.Vec2d.zero()
        tank.body.angular_velocity = 0
        tank.body.angle = tank.start_angle
        tank.flag = None
    # Resets the flag
    flag.is_on_tank = False
    flag.x = flag.start_position[0]
    flag.y = flag.start_position[1]
    # Resets all the boxes by removing them and spawning in them as if the game has started again
    for box in reversed(game_objects_list):
        if isinstance(box, gameobjects.Box):
            game_objects_list.remove(box)
            space.remove(box.body)
            space.remove(box.shape)
    create_boxes()
    # Resets ai
    for bot in ai_list:
        bot.forced_reset = True
        bot.target_tile = None
        bot.other_path = False


def master_loop():
    """
    Runs the entire program
    """
    exit_game = False
    currently_running = "welcome"
    while not exit_game:
        if currently_running == "main":
            exit_game, currently_running = main_loop()
        elif currently_running == "welcome":
            selected_map, selected_difficulty, exit_game = screens.welcome_screen(currently_running, exit_game, json_map)
            currently_running = initialization(selected_map, selected_difficulty)
        elif currently_running == "score":
            currently_running = screens.score_screen(tanks_list, screen, current_map)
        elif currently_running == "victory":
            exit_game = screens.victory_screen(tanks_list, screen, current_map)


def check_win_conditions():
    """
    Checks if win conditions have been achieved
    """
    POINTS_TO_WIN = 1
    GAME_TIME_LIMIT = FRAMERATE * 60 * 5  # 5 Minutes
    NUMBER_OF_ROUNDS_LIMIT = 10

    # Checks if someone has won by points
    for tank in tanks_list:
        if tank.score == POINTS_TO_WIN:
            return True

    # Checks if time limit is reached
    if total_game_time > GAME_TIME_LIMIT:
        return True

    # Checks if round limit is reached
    if total_round_number == NUMBER_OF_ROUNDS_LIMIT:
        return True


def main_loop():
    """
    Runs main loop of the game.
    """
    # --Control whether the game run
    running = True
    global total_game_time
    global total_round_number
    skip_update = 0
    bullet_tick = 50
    screen_black = fog_of_war((0, 0, 0))
    exit_game = False
    while running:
        # --Handle the events
        for event in pygame.event.get():
            # Check if we receive a QUIT event (for instance, if the user press the
            # close button of the wiendow) or if the user press the escape key.
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                exit_game = True
                running = False
            # --Controls for player tank
            # Moves or turns the tank when corresponding key is pressed
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    tanks_list[0].accelerate()
                elif event.key == K_DOWN:
                    tanks_list[0].decelerate()
                elif event.key == K_RIGHT:
                    tanks_list[0].turn_right()
                elif event.key == K_LEFT:
                    tanks_list[0].turn_left()
                elif event.key == K_SPACE and bullet_tick == 50:
                    game_objects_list.append(tanks_list[0].shoot(space))
                    bullet_tick = 0
            # Stops the tanks
            elif event.type == KEYUP:
                # Stops turning when right or left arent pressed
                if event.key == K_RIGHT or event.key == K_LEFT:
                    tanks_list[0].stop_turning()
                # Stops moving when up or down arent pressed
                elif event.key == K_UP or event.key == K_DOWN:
                    tanks_list[0].stop_moving()

        # Cooldown for bullet
        if (bullet_tick != 50):
            bullet_tick += 1

        # -- Loops through tanks_list
        for tank in tanks_list:
            # Tries to grab the flag
            tank.try_grab_flag(flag)
            # Checks if the tank has won
            if tank.has_won():
                tank.score += 1
                reset_game()
                running = False
                total_round_number += 1
                currently_running = "score"

        # --Loops through ai_list
        for bot in ai_list:
            # Calls decide function for each ai instance and ignores player
            if not bot.tank == tanks_list[0]:
                bot.decide()
            # Makes the ai shoot
            if bot.has_fired:
                bot.has_fired = False
                game_objects_list.append(bot.tank.shoot(space))
            if bot.tank.flag is not None:
                shortest_path = ai.Ai.reveal_position(self=bot, start=bot.tank.start_position)
                for bot in ai_list:
                    bot.target_tile = shortest_path

        # Runs collisions
        handler_bullet_tank.post_solve = collision_bullet_tank
        handler_bullet_box.pre_solve = collision_bullet_box
        handler_bullet_boundry.post_solve = collision_bullet_boundry

        # --Update physics
        if skip_update == 0:
            # Loop over all the game objects and update their speed in function of their
            # acceleration.
            for obj in game_objects_list:
                obj.update()
            skip_update = 2
        else:
            skip_update -= 1

        # Check collisions and update the objects position
        space.step(1 / FRAMERATE)

        # Update object that depends on an other object position (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()

        # --Update Display

        # Displays the background on the screen
        screen.blit(background, (0, 0))

        # Update the display of the game objects on the screen
        screen_black.fill((0, 0, 0))
        for obj in game_objects_list:
            obj.update_screen(screen)
            if isinstance(obj, gameobjects.Tank):
                if obj.circle == []:
                    obj.circle.append(pygame.draw.circle(screen_black, (69, 69, 69), obj.body.position * images.TILE_SIZE, 80))
                else:
                    obj.circle.pop()
                    obj.circle.append(pygame.draw.circle(screen_black, (69, 69, 69), obj.body.position * images.TILE_SIZE, 80))

        # Display fog of war on the screen
        screen.blit(screen_black, (0, 0))
        screen_black.set_colorkey((69, 69, 69))

        # Redisplay the entire screen (see double buffer technique)
        pygame.display.flip()

        # Updates the total game time
        total_game_time += 1

        # Checks if someone has won the game
        if check_win_conditions():
            running = False
            currently_running = "victory"

        # Control the game framerate
        clock.tick(FRAMERATE)
    return exit_game, currently_running


# Runs the game
master_loop()
