import pygame
import sys
import random
import heapq

pygame.init()

font_size = 32
grid_w = 40
grid_h = 20
log_size = 8
top_bar_size = 2
font = pygame.font.SysFont("Consolas", font_size)
screen = pygame.display.set_mode((grid_w * font_size, grid_h * font_size + (log_size * font_size) + (top_bar_size * font_size)))
clock = pygame.time.Clock()


def find_valid_spawn(grid):

    height = len(grid)
    width = len(grid[0])

    while True:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if grid[y][x] == ".":
            return (x, y)

def find_up_stairs(grid):
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] == "<":
                return (x, y)
    return None
def find_down_stairs(grid):
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] == ">":
                return (x, y)
    return None

# cheap function to create 2d array
def create_floor():
    grid = [["#" for _ in range(grid_w)] for _ in range(grid_h)]
    rooms = []

    room_count = random.randint(5, 10)
    room_min_size = 5
    room_max_size = 10

    for _ in range(room_count):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(1, grid_w - w - 2)
        y = random.randint(1, grid_h - h - 2)

        # store the center for connecting later
        center = (x + w // 2, y + h // 2)
        rooms.append(center)

        # carve out the room
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                grid[yy][xx] = "."

    for i in range(1, len(rooms)):
        x1, y1 = rooms[i - 1]
        x2, y2 = rooms[i]

        if random.random() < 0.5:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                grid[y1][x] = "."
            for y in range(min(y1, y2), max(y1, y2) + 1):
                grid[y][x2] = "."
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                grid[y][x1] = "."
            for x in range(min(x1, x2), max(x1, x2) + 1):
                grid[y2][x] = "."

    ## add stairs < and >
    stair_up_x, stair_up_y = find_valid_spawn(grid)
    grid[stair_up_y][stair_up_x] = "<"
    stair_down_x, stair_down_y = find_valid_spawn(grid)
    grid[stair_down_y][stair_down_x] = ">"
    return grid


class Ai:
    def __init__(self, owner):
        self.owner = owner

    def take_turn(self, world):
        pass


class WonderAi(Ai):
    def take_turn(self, world):
        x, y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        world.move_entity(self.owner, x, y)


class ChaseAi(Ai):
    def take_turn(self, world):
        player = world.player
        x = 0 if player.x == self.owner.x else (1 if player.x > self.owner.x else -1)
        y = 0 if player.y == self.owner.y else (1 if player.y > self.owner.y else -1)
        world.move_entity(self.owner, x, y)


class AStar(Ai):
    def take_turn(self, world):
        player = world.player
        start = (self.owner.x, self.owner.y)
        goal = (player.x, player.y)
        path = astar_path(world, start, goal)
        if path and len(path) > 1:
            next_step = path[1]
            x = next_step[0] - self.owner.x
            y = next_step[1] - self.owner.y
            world.move_entity(self.owner, x, y)


class ChaseAndWonderAi(Ai):
    def take_turn(self, world):
        if random.random() < 0.5:
            # chase
            player = world.player
            x = 0 if player.x == self.owner.x else (1 if player.x > self.owner.x else -1)
            y = 0 if player.y == self.owner.y else (1 if player.y > self.owner.y else -1)
            world.move_entity(self.owner, x, y)
        else:
            # wonder
            x, y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            world.move_entity(self.owner, x, y)


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_path(world, start, goal):
    height = len(world.map)
    width = len(world.map[0])


    def in_bounds(pos):
        x, y = pos
        return 0 <= x < width and 0 <= y < height

    def passable(pos):
        x, y = pos
        return world.is_movable(x, y)

    # 8 directions (N, S, E, W, diagonals)
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
    ]

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {start: None}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # reconstruct path
            path = []
            while current:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if not in_bounds(neighbor) or not passable(neighbor):
                continue

            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None



class Entity:
    def __init__(self, name, x, y, health, attack, symbol, ai=None):
        self.name = name
        self.x = x
        self.y = y
        self.max_health = health
        self.health = health
        self.symbol = symbol
        self.attack = attack
        self.level = 1
        self.experience_to_level = 100
        self.experience = 0
        self.dead = False
        self.ai = ai
        self.ex_gain = 10  # experience given when killed
        self.score = 0
        if self.ai:
            self.ai.owner = self

    def level_up(self):
        self.level += 1
        self.max_health += 10
        self.attack += 2
        self.health = self.max_health
        self.experience = 0
        self.experience_to_level = int(self.experience_to_level * 1.5)

    def set_ex(self,amount):
        self.ex_gain = amount

# prolly want to make this more generic in the future??
# maybe add it to the world class?
def create_random_mob():
    mob_type = random.choice(["orc", "snake", "rat", "astar"])
    return create_mob(mob_type)

def create_mob(name):
    if name == "orc":
        mob = Entity("orc", 0, 0, 10, 3, "O", ai=ChaseAi(None))
        mob.set_ex(20)
        return mob
    elif name == "snake":
        mob = Entity("snake", 0, 0, 5, 2, "S", ai=ChaseAndWonderAi(None))
        mob.set_ex(10)
        return mob
    elif name == "rat":
        mob = Entity("rat", 0, 0, 3, 1, "r", ai=WonderAi(None))
        mob.set_ex(5)
        return mob
    elif name == "astar":
        mob = Entity("astar", 0, 0, 3, 1, "A", ai=AStar(None))
        mob.set_ex(5)
        return mob
    else:
        return None

class World:
    def __init__(self, player):
        self.player = player
        self.map = create_floor()
        self.entities = []
        self.add_entity(player)
        self.log = []
        self.current_floor = 0
        self.floors = [self.map]

    def draw(self):
        screen.fill((0, 0, 0))
        color = (255, 255, 255)

        # stores entity's location to get drawn
        entity_map = {}
        for entity in self.entities:
            pos = (entity.y, entity.x)
            symbol = entity.symbol
            entity_map[pos] = symbol

        height = len(self.map)
        width = len(self.map[0])

        def wall_visible(yy, xx):
            if self.map[yy][xx] != "#":
                return False
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = yy + dy, xx + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if self.map[ny][nx] == ".":
                        return True
            return False

        top_bar_size_offset = (top_bar_size + 1) * font_size

        text = font.render(f"Name: {self.player.name} LVL: {str(self.player.level)} HP: {str(self.player.health)} EX: {str(self.player.experience)}/{str(self.player.experience_to_level)} Attack: {str(self.player.attack)}", True, color)
        screen.blit(text, (0, font_size))
        text = font.render(f"Floor: {self.current_floor} Score: {str(self.player.score)} | Press ? for help", True, color)
        screen.blit(text, (0, font_size * 2))

        for y, row in enumerate(self.map):
            for x, ch in enumerate(row):
                if (y, x) in entity_map:
                    if entity_map[(y, x)] == "@":
                        text = font.render("@", True, (0, 255, 0))
                        screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))
                    else:
                        text = font.render(entity_map[(y, x)], True, color)
                        screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))
                else:
                    if ch == "#":
                        if wall_visible(y, x):
                            text = font.render("#", True, color)
                        else:
                            text = font.render(" ", True, color)

                    else:
                        text = font.render(ch, True, color)
                    screen.blit(text, (x * font_size, y * font_size + top_bar_size_offset))

        # draw log
        log_start_y = grid_h * font_size
        for i, log_entry in enumerate(self.log[-log_size:]):
            text = font.render(log_entry, True, color)
            screen.blit(text, (0, log_start_y + i * font_size + top_bar_size_offset))
            
    def log_message(self, message):
        self.log.append(message)    

    def is_movable(self, x, y):
        return self.map[y][x] != "#"

    def move_entity(self, entity, x, y):
        # check for walls and other stuff here
        new_x = entity.x + x
        new_y = entity.y + y

        if not self.is_movable(new_x, new_y):
            return

        for e in self.entities:
            if e is not entity and e.x == new_x and e.y == new_y:
                # attack seq (entity then other: e)
                e.health -= entity.attack
                self.log_message(f"{entity.name} attacks {e.name} for {entity.attack}!")
                if e.health <= 0:
                    self.log_message(f"{e.name} dies!")
                    e.dead = True
                    entity.experience += e.ex_gain
                    self.log_message(f"{entity.name} gains {e.ex_gain} experience!")
                    entity.score += e.ex_gain
                    if entity.experience >= entity.experience_to_level:
                        entity.level_up()
                        self.log_message(f"{entity.name} levels up to level {entity.level}!")
                        entity.score += 50
                if entity.health <= 0:
                    self.log_message(f"{entity.name} dies!")
                    entity.dead = True
                return

        entity.x = new_x
        entity.y = new_y

    def go_down_stairs(self):
        # check if all entities are dead on the floor
        for e in self.entities:
            if e is not self.player and not e.dead:
                self.log_message("You must defeat all enemies on this floor before descending!")
                return
        
        if self.current_floor + 1 >= len(self.floors):
            new_floor = create_floor()
            # fill with mobs
            for _ in range(random.randint(5, 15)):
                mob = create_random_mob()
                x, y = find_valid_spawn(new_floor)
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

                self.entities.append(mob)
            self.floors.append(new_floor)
        else:
            new_floor = self.floors[self.current_floor + 1]

        self.current_floor += 1
        self.map = self.floors[self.current_floor]
        self.player.x, self.player.y = find_up_stairs(self.map)


    def go_up_stairs(self):
        if self.current_floor == 0:
            self.log_message("You are already on the first floor!")
            return  # can't go up from first floor

        self.current_floor -= 1
        self.map = self.floors[self.current_floor]
        self.player.x, self.player.y = find_down_stairs(self.map)

    def update(self):
        # move the mobs
        for e in list(self.entities):
            if e.ai and not e.dead:
                e.ai.take_turn(self)

        self.entities = [e for e in self.entities if not e.dead]

    def add_entity(self, entity):
        x,y = find_valid_spawn(self.map)
        entity.x = x
        entity.y = y
        self.entities.append(entity)


player = Entity("player", 5, 5, 100, 5, "@")
world = World(player)

for _ in range(15):
    mob = create_random_mob()
    world.add_entity(mob)

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
                                player = Entity("player", 5, 5, 100, 5, "@")
                                world = World(player)
                                for _ in range(10):
                                    mob = create_random_mob()
                                    world.add_entity(mob)
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
                world.move_entity(player, 0, -1)
            elif event.key == pygame.K_DOWN:
                world.move_entity(player, 0, 1)
            elif event.key == pygame.K_RIGHT:
                world.move_entity(player, 1, 0)
            elif event.key == pygame.K_LEFT:
                world.move_entity(player, -1, 0)

            # vim style keybinds 
            elif event.key == pygame.K_k:
                world.move_entity(player, 0, -1)
            elif event.key == pygame.K_j:
                world.move_entity(player, 0, 1)
            elif event.key == pygame.K_l:
                world.move_entity(player, 1, 0)
            elif event.key == pygame.K_h:
                world.move_entity(player, -1, 0)


            # go down stairs
            elif event.key == pygame.K_PERIOD:
                if world.map[player.y][player.x] == ">":
                    world.go_down_stairs()
            # go up stairs
            elif event.key == pygame.K_COMMA:
                if world.map[player.y][player.x] == "<":
                    world.go_up_stairs()

            # reset keys
            elif event.key == pygame.K_r:
                world = World(player)
                for _ in range(10):
                    mob = create_random_mob()
                    world.add_entity(mob)

            # update when player moves
            world.update()

    world.draw()

    pygame.display.flip()
    clock.tick(30)
