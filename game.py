import pygame
import sys
import random
import heapq

from entities import Entity, create_random_mob

from floor import Floor, find_down_stairs, find_up_stairs, find_valid_spawn


class World:
    def __init__(self, player):
        self.player = player
        self.floors = [Floor(self, grid_w, grid_h)]
        self.log = []
        self.current_floor = 0
        
        self.map.add_entity(player)
        
        for _ in range(15):
            mob = create_random_mob()
            self.map.add_entity(mob)
    
    
    @property
    def map(self):
        return self.floors[self.current_floor]

    def go_down_stairs(self):
        if self.current_floor == len(self.floors) - 1:
            new_floor = Floor(self, grid_w, grid_h)
            # fill with mobs
            for _ in range(random.randint(5, 15)):
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

                # level up mob based on floor randomly
                for _ in range(random.randint(1, self.current_floor + 1)):
                    mob.level_up()

                mob.set_ex(mob.ex_gain + self.current_floor * 5)

                new_floor.entities.append(mob)
            
            new_floor.add_entity(self.player)
                
            self.floors.append(new_floor)

        self.current_floor += 1
        self.player.x, self.player.y = find_up_stairs(self.map.grid)
    
    
    def go_up_stairs(self):
        self.current_floor -= 1
        self.player.x, self.player.y = find_down_stairs(self.map.grid)

        
    
    def log_message(self, message):
        self.log.append(message)
        
    def update(self):
        self.map.update()
    
    def draw(self):
        screen.fill((0, 0, 0))
        color = (255, 255, 255)

        # stores entity's location to get drawn
        entity_map = {}
        for entity in self.map.entities:
            pos = (entity.y, entity.x)
            symbol = (entity.symbol, entity.color)
            entity_map[pos] = symbol

        # stores entity's location to get drawn
        item_map = {}
        for item in self.map.items:
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

        top_bar_size_offset = (top_bar_size + 1) * font_size

        text = font.render(f"Name: {self.player.name} LVL: {str(self.player.level)} HP: {str(self.player.health)} EX: {str(self.player.experience)}/{str(self.player.experience_to_level)} Attack: {str(self.player.attack)}", True, color)
        screen.blit(text, (0, font_size))
        text = font.render(f"Floor: {self.current_floor} Score: {str(self.player.score)} | Press ? for help", True, color)
        screen.blit(text, (0, font_size * 2))
    
        for y, row in enumerate(self.map.grid):
            for x, ch in enumerate(row):
                if (y, x) in entity_map:
                    if entity_map[(y, x)][1] == "@":
                        text = font.render("@", True, (0, 255, 0))
                        screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))
                    else:
                        text = font.render(str(entity_map[(y, x)][0]), True, entity_map[(y,x)][1])
                        screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))
                elif (y, x) in item_map:
                    text = font.render(str(item_map[(y, x)][0]), True, item_map[(y,x)][1])
                    screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))
                else:
                    if ch == "#":
                        if wall_visible(y, x):
                            text = font.render("#", True, color)
                        else:
                            text = font.render(" ", True, color)
                    elif ch == "<":
                        if world.current_floor == 0:
                            text = font.render(".", True, color)
                        elif world.current_floor == 1:
                            text = font.render("<", True, (255, 215, 0))
                    elif ch == ">":
                        text = font.render(">", True, (255, 215, 0))
                    else:
                        text = font.render(ch, True, color)
                    screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))

        # draw log
        log_start_y = grid_h * font_size
        for i, log_entry in enumerate(self.log[-log_size:]):
            text = font.render(log_entry, True, color)
            screen.blit(text, (0, log_start_y + i * font_size + top_bar_size_offset))
            

pygame.init()

font_size = 32
grid_w = 40
grid_h = 20
log_size = 8
top_bar_size = 2
font = pygame.font.SysFont("Consolas", font_size)
screen = pygame.display.set_mode((grid_w * font_size, grid_h * font_size + (log_size * font_size) + (top_bar_size * font_size)))
clock = pygame.time.Clock()

player = Entity("player", 5, 5, 100, 5, (0,255,0), "@")
world = World(player)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

            # if player is dead, show death screen and only accept restart
            if player.dead:
                screen.fill((0, 0, 0))
                # print dead screen
                text = font.render("You died!", True, (255, 0, 0))
                screen.blit(text, (grid_w * font_size // 2 - text.get_width() // 2, grid_h * font_size // 2))
                # show restart option
                text = font.render("Press R to restart", True, (255, 255, 255))
                screen.blit(text, (grid_w * font_size // 2 - text.get_width() // 2, grid_h * font_size // 2 + font_size))
                pygame.display.flip()
                # wait for player to press R or quit
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                player = Entity("player", 5, 5, 100, 5, (0,255,0), "@")
                                world = World(player)
                                waiting = False
                # skip movement and updates while dead
                continue
            

            # press ? for help menu
            if event.key == pygame.K_SLASH or event.key == pygame.K_QUESTION:
                screen.fill((0, 0, 0))
                help_lines = [
                    "Controls:",
                    "Arrow Keys / HJKL: Move",
                    "., : Go Down/Up Stairs",
                    "R: Restart Game",
                    "Q / ESC: Quit Game",
                    "",
                    "Press any key to return..."
                ]
                for i, line in enumerate(help_lines):
                    text = font.render(line, True, (255, 255, 255))
                    screen.blit(text, (50, 50 + i * font_size))
                pygame.display.flip()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            waiting = False
                continue

            # janky pygame coord x right, -x left, y down, -y up
            if event.key == pygame.K_UP:
                world.map.move_entity(player, 0, -1)
            elif event.key == pygame.K_DOWN:
                world.map.move_entity(player, 0, 1)
            elif event.key == pygame.K_RIGHT:
                world.map.move_entity(player, 1, 0)
            elif event.key == pygame.K_LEFT:
                world.map.move_entity(player, -1, 0)

            # vim style keybinds 
            elif event.key == pygame.K_k:
                world.map.move_entity(player, 0, -1)
            elif event.key == pygame.K_j:
                world.map.move_entity(player, 0, 1)
            elif event.key == pygame.K_l:
                world.map.move_entity(player, 1, 0)
            elif event.key == pygame.K_h:
                world.map.move_entity(player, -1, 0)


            # go down stairs
            elif event.key == pygame.K_PERIOD:
                if world.map.grid[player.y][player.x] == ">":
                    world.go_down_stairs()
            # go up stairs
            elif event.key == pygame.K_COMMA and world.current_floor > 0:
                if world.map.grid[player.y][player.x] == "<":
                    world.go_up_stairs()

            # reset keys
            elif event.key == pygame.K_r:
                world = World(player)

            # update when player moves
            world.update()

    world.draw()

    pygame.display.flip()
    clock.tick(30)
