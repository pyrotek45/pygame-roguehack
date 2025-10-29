import random
import heapq

# -------------------- Classes & API -------------------- #

class Entity:
    def __init__(self, name, x, y, health, attack, symbol, color, ai=None):
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
        self.color = color
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


class Ai:
    def __init__(self, owner):
        self.owner = owner

    def take_turn(self, world):
        pass



# prolly want to make this more generic in the future??
# maybe add it to the world class?
def create_random_mob():
    mob_type = random.choice(["orc", "snake", "rat"])
    return create_mob(mob_type)


def create_mob(name):
    if name == "orc":
        mob = Entity("orc", 0, 0, 10, 3, "O", (200,200,200), ai=AStarAi(None))
        mob.set_ex(20)
        return mob
    elif name == "snake":
        mob = Entity("snake", 0, 0, 5, 2, "S", (100,100,100), ai=ChaseAndWonderAi(None))
        mob.set_ex(10)
        return mob
    elif name == "rat":
        mob = Entity("rat", 0, 0, 3, 1, "r", (150,100,150), ai=WonderAi(None))
        mob.set_ex(5)
        return mob
    else:
        return None



# ----------------- AI Implementations ---------------- #

    
class WonderAi(Ai):
    def take_turn(self, floor):
        x, y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        floor.move_entity(self.owner, x, y)


class ChaseAi(Ai):
    def take_turn(self, floor):
        player = floor.world.player
        x = 0 if player.x == self.owner.x else (1 if player.x > self.owner.x else -1)
        y = 0 if player.y == self.owner.y else (1 if player.y > self.owner.y else -1)
        floor.move_entity(self.owner, x, y)


class AStarAi(Ai):
    def take_turn(self, floor):
        player = floor.world.player
        start = (self.owner.x, self.owner.y)
        goal = (player.x, player.y)
        path = astar_path(floor, start, goal)
        if path and len(path) > 1:
            next_step = path[1]
            x = next_step[0] - self.owner.x
            y = next_step[1] - self.owner.y
            floor.move_entity(self.owner, x, y)


class ChaseAndWonderAi(Ai):
    def take_turn(self, floor):
        if random.random() < 0.5:
            # chase
            player = floor.world.player
            x = 0 if player.x == self.owner.x else (1 if player.x > self.owner.x else -1)
            y = 0 if player.y == self.owner.y else (1 if player.y > self.owner.y else -1)
            floor.move_entity(self.owner, x, y)
        else:
            # wonder
            x, y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            floor.move_entity(self.owner, x, y)


# ----------------- Pathfinding ---------------- #

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_path(world, start, goal):
    height = len(world.grid)
    width = len(world.grid[0])


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
