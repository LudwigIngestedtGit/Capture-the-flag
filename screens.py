import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
import images
import maps
import time


def generate_map_preview(screen, selected_map, json_map=None):
    """
    Generates preview of map for selection in welcome screen
    """
    width = screen.get_width()
    height = screen.get_height()

    tile_scaled_size = 15
    grass = pygame.transform.scale(images.grass, (tile_scaled_size, tile_scaled_size))
    rockbox = pygame.transform.scale(images.rockbox, (tile_scaled_size, tile_scaled_size))
    woodbox = pygame.transform.scale(images.woodbox, (tile_scaled_size, tile_scaled_size))
    metalbox = pygame.transform.scale(images.metalbox, (tile_scaled_size, tile_scaled_size))

    if selected_map == "map0":
        current_map = maps.map0
    elif selected_map == "map1":
        current_map = maps.map1
    elif selected_map == "map2":
        current_map = maps.map2
    elif selected_map == "json_map":
        current_map = json_map
    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            if current_map.boxAt(x, y) == 0:
                screen.blit(grass, (x * tile_scaled_size - current_map.width * tile_scaled_size / 2 + width / 2, y * tile_scaled_size + height / 2 + 180))
            elif current_map.boxAt(x, y) == 1:
                screen.blit(rockbox, (x * tile_scaled_size - current_map.width * tile_scaled_size / 2 + width / 2, y * tile_scaled_size + height / 2 + 180))
            elif current_map.boxAt(x, y) == 2:
                screen.blit(woodbox, (x * tile_scaled_size - current_map.width * tile_scaled_size / 2 + width / 2, y * tile_scaled_size + height / 2 + 180))
            elif current_map.boxAt(x, y) == 3:
                screen.blit(metalbox, (x * tile_scaled_size - current_map.width * tile_scaled_size / 2 + width / 2, y * tile_scaled_size + height / 2 + 180))


def welcome_screen(currently_running, exit_game, json_map=None):
    """
    Displays welcome screen from which maps and difficulty can be chosen
    """
    # Resolution of the welcome screen
    resolution = (720, 720)

    # Color variables
    text_color = (255, 255, 255)
    unselected_button_color = (100, 100, 100)
    selected_button_color = (255, 102, 0)

    selected_button_index = 0
    buttons = ["start", "maps", "difficulty"]
    selected_map_index = 0
    maps_list = ["map0", "map1", "map2"]
    if json_map is not None:
        maps_list.append("json_map")
    selected_difficulty_index = 1
    difficulty_list = ["easy", "normal", "hard"]

    # Title image
    title = pygame.transform.scale(images.title, (images.title.get_width() * 5, images.title.get_height() * 5))

    # Text variables
    button_font = pygame.font.SysFont(None, 35)
    start_text = button_font.render("start", True, text_color)
    maps_text = button_font.render("maps", True, text_color)

    # Screen variables
    screen = pygame.display.set_mode(resolution)
    width = screen.get_width()
    height = screen.get_height()
    running = True

    # Welcome screen loop
    while running:
        screen.fill((0, 0, 0))

        currently_selected_button = buttons[selected_button_index]
        selected_map = maps_list[selected_map_index]
        selected_difficulty = difficulty_list[selected_difficulty_index]
        difficulty_text = button_font.render(selected_difficulty, True, text_color)
        selected_map_text = button_font.render(selected_map, True, text_color)

        # Draws title
        screen.blit(title, ((width - title.get_width()) / 2, height / 4))

        # --Draws buttons on the screen
        # Draws start button
        if currently_selected_button != "start":
            pygame.draw.rect(screen, unselected_button_color, [width / 2 - 70, height / 2, 140, 40])
        else:
            pygame.draw.rect(screen, selected_button_color, [width / 2 - 70, height / 2, 140, 40])
        screen.blit(start_text, ((width - start_text.get_width()) / 2, height / 2))

        # Draws maps button
        if currently_selected_button != "maps":
            pygame.draw.rect(screen, unselected_button_color, [width / 2 - 70, height / 2 + 50, 140, 40])
        else:
            pygame.draw.rect(screen, selected_button_color, [width / 2 - 70, height / 2 + 50, 140, 40])
        screen.blit(maps_text, ((width - maps_text.get_width()) / 2, height / 2 + 50))

        # Draws difficulty button
        if currently_selected_button != "difficulty":
            pygame.draw.rect(screen, unselected_button_color, [width / 2 - 70, height / 2 + 100, 140, 40])
        else:
            pygame.draw.rect(screen, selected_button_color, [width / 2 - 70, height / 2 + 100, 140, 40])
        screen.blit(difficulty_text, ((width - difficulty_text.get_width()) / 2, height / 2 + 100))

        # Controls for settings and button pressing
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                exit_game = True
                running = False

            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    if selected_button_index == 0:
                        selected_button_index = len(buttons) - 1
                    else:
                        selected_button_index -= 1

                if event.key == K_DOWN:
                    if selected_button_index == len(buttons) - 1:
                        selected_button_index = 0
                    else:
                        selected_button_index += 1

                if event.key == K_LEFT:
                    if currently_selected_button == "maps":
                        if selected_map_index == 0:
                            selected_map_index = len(maps_list) - 1
                        else:
                            selected_map_index -= 1

                    if currently_selected_button == "difficulty":
                        if selected_difficulty_index == 0:
                            selected_difficulty_index = len(difficulty_list) - 1
                        else:
                            selected_difficulty_index -= 1

                if event.key == K_RIGHT:
                    if currently_selected_button == "maps":
                        if selected_map_index == len(maps_list) - 1:
                            selected_map_index = 0
                        else:
                            selected_map_index += 1

                    if currently_selected_button == "difficulty":
                        if selected_difficulty_index == len(difficulty_list) - 1:
                            selected_difficulty_index = 0
                        else:
                            selected_difficulty_index += 1

                if event.key == K_RETURN:
                    if currently_selected_button == "start":
                        running = False

        if running:
            # Draws map preview and map name
            screen.blit(selected_map_text, ((width - selected_map_text.get_width()) / 2, height / 2 + 150))
            generate_map_preview(screen, selected_map, json_map)

        pygame.display.update()
    return selected_map, selected_difficulty, exit_game


def victory_screen(tanks_list, screen, current_map):
    """
    Displays victory screen
    """
    # Checks who won (if multiple people won it will show them all)
    current_highest_score = 0
    winners_text = []
    white = (255, 255, 255)
    dark_grey = (50, 50, 50)
    for tank in tanks_list:
        if tank.score > current_highest_score:
            current_highest_score = tank.score
    for tank in tanks_list:
        if tank.score == current_highest_score:
            winners_text.append("Winner Player" + str(tank.player_number))

    # --Draws the victory screen
    # Draws the background
    pygame.display.set_caption("Capture the flag")
    screen.fill(dark_grey)

    # Draws a crown
    center_x = current_map.rect().size[0] // 2
    center_y = current_map.rect().size[1] // 2
    screen.blit(images.crown, (center_x - (images.crown.get_width() // 2), center_y + -175))
    # Draws the winners
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    for y in range(len(winners_text)):
        text = font.render(winners_text[y], True, white)
        textRect = text.get_rect()
        textRect.center = (current_map.rect().size[0] // 2, current_map.rect().size[1] // 2 + 50 + 25 * y - 25 * (len(winners_text) / 2))
        screen.blit(text, textRect)
    pygame.display.flip()

    # Exits the game
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                exit_game = True
                running = False
    return exit_game


def score_screen(tanks_list, screen, current_map):
    """
    Displays score screen inbetween games
    """
    # Creates all the text to be displayed aswell as the font
    white = (255, 255, 255)
    grey = (100, 100, 100)
    score_text = []
    player_number = 0
    for tank in tanks_list:
        player_number += 1
        score_text.append("Player " + str(player_number) + ": " + str(tank.score))
    pygame.display.set_caption("Capture the flag")
    font = pygame.font.Font(pygame.font.get_default_font(), 20)

    # Draws the scoreboard
    screen.fill(grey)
    for y in range(len(tanks_list)):
        text = font.render(score_text[y], True, white)
        textRect = text.get_rect()
        textRect.center = (current_map.rect().size[0] // 2, current_map.rect().size[1] // 2 + 25 * y - 25 * (len(tanks_list) / 2))
        screen.blit(text, textRect)
    pygame.display.flip()

    # Shows the score screen for 4 seconds
    time.sleep(4)
    currently_running = "main"
    return currently_running
