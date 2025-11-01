import random


class Item:
    def __init__(self, x, y, name, symbol, color):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.name = name
        self.color = color
        self.used = False

    def use(self, entity, world):
        pass


# gets used as soon as stepped on
class Potion(Item):
    def use(self, entity, world):
        entity.health += 20
        if entity.health > entity.max_health:
            entity.health = entity.max_health

        self.used = True
        world.log_message(f"{entity.name} gained 20 health from potion")


class System:
    def __init__(self):
        pass

    def run(self, floor):
        pass


class EntitySystem(System):
    def run(self, floor):
        for e in list(floor.components["entities"]):
            if e.ai and not e.dead:
                e.ai.take_turn(floor)

        floor.components["entities"] = [
            e for e in floor.components["entities"] if not e.dead
        ]


class Floor:
    def __init__(self, world, grid_w, grid_h):
        self.grid = self.create_floor(grid_w, grid_h)
        self.world = world

        self.components = {"entities": [], "items": []}

        self.systems = [EntitySystem()]

        # add some potions to the floor
        for _ in range(3):
            self.add_component("items", Potion(0, 0, "Potion", "P", (140, 255, 200)))

    def create_floor(self, grid_w, grid_h):
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

    def is_movable(self, x, y):
        return self.grid[y][x] != "#"

    def move_entity(self, entity, x, y):
        # check for walls and other stuff here
        new_x = entity.x + x
        new_y = entity.y + y

        if not self.is_movable(new_x, new_y):
            return

        for e in self.components["entities"]:
            if e is not entity and e.x == new_x and e.y == new_y:
                # attack seq (entity then other: e)
                e.health -= entity.attack
                self.world.log_message(
                    f"{entity.name} attacks {e.name} for {entity.attack}!"
                )
                if e.health <= 0:
                    self.world.log_message(f"{e.name} dies!")
                    e.dead = True
                    entity.experience += e.ex_gain
                    self.world.log_message(
                        f"{entity.name} gains {e.ex_gain} experience!"
                    )
                    entity.score += e.ex_gain
                    if entity.experience >= entity.experience_to_level:
                        entity.level_up()
                        self.world.log_message(
                            f"{entity.name} levels up to level {entity.level}!"
                        )
                        entity.score += 50
                    if entity.health <= 0:
                        self.world.log_message(f"{entity.name} dies!")
                        entity.dead = True
                return

        for i in self.components["items"]:
            if not i.used and i.x == new_x and i.y == new_y:
                i.use(entity, self.world)

        entity.x = new_x
        entity.y = new_y

    def update(self):
        for system in self.systems:
            system.run(self)

    def add_system(self, system):
        self.systems.append(system)

    def add_component(self, component, value=None):
        if component in self.components:
            if value:
                if hasattr(value, "x") and hasattr(value, "y"):
                    x, y = find_valid_spawn(self.grid)
                    value.x = x
                    value.y = y
                    self.components[component].append(value)
                else:
                    self.components[component].append(value)

        else:
            self.components[component] = []


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
