import pygame
import sys
import random

from enum import Enum, auto
from entities import Entity, create_random_mob
from floor import Floor, find_down_stairs, find_up_stairs, find_valid_spawn

pygame.init()

FONTSIZE = 32
GRID_W = 40
GRID_H = 20
LOG_SIZE = 8
TOP_BAR_SIZE = 2

font = pygame.font.SysFont("Consolas", FONTSIZE)
screen = pygame.display.set_mode(
    (
        GRID_W * FONTSIZE,
        GRID_H * FONTSIZE + (LOG_SIZE * FONTSIZE) + (TOP_BAR_SIZE * FONTSIZE),
    )
)
clock = pygame.time.Clock()


class State(Enum):
    GAMEOVER = auto()
    OVERWORLD = auto()
    HELP = auto()


class World:
    def __init__(self):
        self.state = State.OVERWORLD

        self.player = Entity("player", 5, 5, 100, 5, (0, 255, 0), "@")

        self.floors = [Floor(self, GRID_W, GRID_H)]
        self.current_floor = 0
        self.add_mobs(3)

        self.log = []

        self.map.add_component("entities", self.player)

    def reset(self):
        self.state = State.OVERWORLD

        self.player = Entity("player", 5, 5, 100, 5, (0, 255, 0), "@")

        self.floors = [Floor(self, GRID_W, GRID_H)]
        self.current_floor = 0
        self.add_mobs(3)

        self.log = []
        self.map.add_component("entitites", self.player)

    def add_mobs(self, num):
        for _ in range(num):
            mob = create_random_mob()
            self.map.add_component("entities", mob)

    @property
    def map(self):
        return self.floors[self.current_floor]

    def go_down_stairs(self):
        if self.current_floor == len(self.floors) - 1:
            new_floor = Floor(self, GRID_W, GRID_H)
            # fill with mobs
            for _ in range(random.randint(1, self.current_floor + 4)):
                mob = create_random_mob()
                x, y = find_valid_spawn(new_floor.grid)
                mob.x = x
                mob.y = y

                # make mobs harder on deeper floors
                attack = mob.attack + self.current_floor
                health = mob.max_health + self.current_floor

                mob.attack = attack
                mob.health = health
                mob.max_health = health

                mob.set_ex(mob.ex_gain + self.current_floor * 2)

                new_floor.add_component("entities", mob)

            new_floor.add_component("entities", self.player)

            self.floors.append(new_floor)

        self.current_floor += 1
        self.player.x, self.player.y = find_up_stairs(self.map.grid)

    def go_up_stairs(self):
        self.current_floor -= 1
        self.player.x, self.player.y = find_down_stairs(self.map.grid)

    # log can only show 8, so perhaps list needs to erase non visable ones, otherwise
    # list could grow and waste memory. unless there is a log history feature at some point?
    def log_message(self, message):
        self.log.append(message)
        while len(self.log) > 9:
            self.log.pop(0)

    def update(self):
        self.map.update()
        if self.player.health <= 0:
            self.state = State.GAMEOVER

    def draw_overworld(self):
        color = (255, 255, 255)
        # stores entity's location to get drawn
        entity_map = {}
        for entity in self.map.components["entities"]:
            pos = (entity.y, entity.x)
            symbol = (entity.symbol, entity.color)
            entity_map[pos] = symbol

        # stores entity's location to get drawn
        item_map = {}
        for item in self.map.components["items"]:
            if not item.used:
                pos = (item.y, item.x)
                symbol = (item.symbol, item.color)
                item_map[pos] = symbol

        height = len(self.map.grid)
        width = len(self.map.grid[0])

        def wall_visible(yy, xx):
            if self.map.grid[yy][xx] != "#":
                return False
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = yy + dy, xx + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if self.map.grid[ny][nx] == ".":
                        return True
            return False

        top_bar_size_offset = (TOP_BAR_SIZE + 1) * FONTSIZE

        text = font.render(
            f"Name: {self.player.name} LVL: {str(self.player.level)} HP: {str(self.player.health)}/{str(self.player.max_health)} EX: {str(self.player.experience)}/{str(self.player.experience_to_level)} Attack: {str(self.player.attack)}",
            True,
            color,
        )
        screen.blit(text, (0, FONTSIZE))
        text = font.render(
            f"Floor: {self.current_floor} Score: {str(self.player.score)} | Press ? for help",
            True,
            color,
        )
        screen.blit(text, (0, FONTSIZE * 2))

        for y, row in enumerate(self.map.grid):
            for x, ch in enumerate(row):
                if (y, x) in entity_map:
                    if entity_map[(y, x)][1] == "@":
                        text = font.render("@", True, (0, 255, 0))
                        screen.blit(
                            text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset)
                        )
                    else:
                        text = font.render(
                            str(entity_map[(y, x)][0]), True, entity_map[(y, x)][1]
                        )
                        screen.blit(
                            text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset)
                        )
                elif (y, x) in item_map:
                    text = font.render(
                        str(item_map[(y, x)][0]), True, item_map[(y, x)][1]
                    )
                    screen.blit(
                        text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset)
                    )
                else:
                    if ch == "#":
                        if wall_visible(y, x):
                            text = font.render("#", True, color)
                        else:
                            text = font.render(" ", True, color)
                    elif ch == "<":
                        if world.current_floor == 0:
                            text = font.render(".", True, color)
                        elif world.current_floor >= 1:
                            text = font.render("<", True, (255, 215, 0))
                    elif ch == ">":
                        text = font.render(">", True, (255, 215, 0))
                    else:
                        text = font.render(ch, True, color)
                    screen.blit(
                        text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset)
                    )

        # draw log
        log_start_y = GRID_H * FONTSIZE
        for i, log_entry in enumerate(self.log[-LOG_SIZE:]):
            text = font.render(log_entry, True, color)
            screen.blit(text, (0, log_start_y + i * FONTSIZE + top_bar_size_offset))

    def draw_gameover(self):
        # print dead screen
        text = font.render("You died!", True, (255, 0, 0))
        screen.blit(
            text,
            (GRID_W * FONTSIZE // 2 - text.get_width() // 2, GRID_H * FONTSIZE // 2),
        )
        # show restart option
        text = font.render("Press R to restart", True, (255, 255, 255))
        screen.blit(
            text,
            (
                GRID_W * FONTSIZE // 2 - text.get_width() // 2,
                GRID_H * FONTSIZE // 2 + FONTSIZE,
            ),
        )

    def draw_help(self):
        help_lines = [
            "Controls:",
            "Arrow Keys / HJKL: Move",
            "., : Go Down/Up Stairs",
            "R: Restart Game",
            "Q / ESC: Quit Game",
            "",
            "Press any key to return...",
        ]
        for i, line in enumerate(help_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, 50 + i * FONTSIZE))

    def draw(self):
        # always reset screen to black
        screen.fill((0, 0, 0))
        match self.state:
            case State.OVERWORLD:
                self.draw_overworld()
            case State.GAMEOVER:
                self.draw_gameover()
            case State.HELP:
                self.draw_help()

    def handle_input(self, input):
        match self.state:
            case State.OVERWORLD:
                match input:
                    case pygame.K_UP:
                        self.map.move_entity(self.player, 0, -1)
                    case pygame.K_DOWN:
                        self.map.move_entity(self.player, 0, 1)
                    case pygame.K_RIGHT:
                        self.map.move_entity(self.player, 1, 0)
                    case pygame.K_LEFT:
                        self.map.move_entity(self.player, -1, 0)

                    case pygame.K_k:
                        self.map.move_entity(self.player, 0, -1)
                    case pygame.K_j:
                        self.map.move_entity(self.player, 0, 1)
                    case pygame.K_l:
                        self.map.move_entity(self.player, 1, 0)
                    case pygame.K_h:
                        self.map.move_entity(self.player, -1, 0)

                    case pygame.K_PERIOD:
                        if self.map.grid[self.player.y][self.player.x] == ">":
                            self.go_down_stairs()

                    case pygame.K_COMMA:
                        if (
                            self.current_floor > 0
                            and world.map.grid[self.player.y][self.player.x] == "<"
                        ):
                            world.go_up_stairs()

                    case pygame.K_r:
                        self.reset()

                    case pygame.K_q:
                        pygame.quit()
                        sys.exit()

                    case pygame.K_SLASH:
                        self.state = State.HELP
                        return

                    case _:
                        pass

                # not every action should update the world
                self.update()

            case State.GAMEOVER:
                match input:
                    case pygame.K_r:
                        self.reset()
                    case _:
                        pass

            case State.HELP:
                match input:
                    case _:
                        self.state = State.OVERWORLD
                pass


# main game setup
world = World()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            world.handle_input(event.key)

    world.draw()

    pygame.display.flip()
    clock.tick(30)
