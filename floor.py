import random
from entities import Entity, WonderAi

class System:
    def __init__(self):
        pass

    def run(self, floor):
        pass


class Potion:
    def __init__(self, x, y, name, symbol, color):
        self.name = name
        self.x = x
        self.y = y
        self.symbol = symbol
        self.color = color
        self.used = False

    def activate(self, entity, world):
        entity.health += 20
        if entity.health > entity.max_health:
            entity.health = entity.max_health

        self.used = True
        world.log_message(f"{entity.name} gained 20 health from potion")


class PostionSystem(System):
    def run(self, floor):
        for i in floor.components["potion"]:
            for entity in floor.components["entities"]:
                if not i.used and i.x == entity.x and i.y == entity.y:
                    i.activate(entity, floor.world)



class EntitySystem(System):
    def run(self, floor):
        for e in floor.components["entities"]:
            if e.ai and not e.dead:
                if e.name == "amoeba":
                    if random.random() > 0.03:
                        e.ai.take_turn(floor)
                    else:
                        directions = [ (1, 0), (-1, 0), (0, 1), (0, -1), ]
                        open_tiles = [dir for dir in directions if floor.grid[e.y + dir[0]][e.x + dir[1]] == "."]
                        if open_tiles:
                            mob = Entity("amoeba", 0, 0, 3, 1, "a", (55, 120, 50), ai=WonderAi(None))
                            floor.add_component("entities", mob)
                            open_tile = random.choice(open_tiles)
                            mob.original = False
                            mob.x = e.x + open_tile[1]
                            mob.y = e.y + open_tile[0]
                            floor.world.log_message("amoeba has replicated")
                else:
                    e.ai.take_turn(floor)

        floor.components["entities"] = [ e for e in floor.components["entities"] if not e.dead and e.health > 0 ]


class ArrowTrap:
    def __init__(self, symbol, x, y, color, lifetime):
        self.name = "arrow trap"
        self.symbol = symbol
        self.x = x
        self.y = y
        self.visable = True
        self.color = color
        self.lifetime = lifetime
        self.direction = random.choice(["up","down","left","right"])

    def tick(self):
        self.lifetime -= 1


class ArrowTrapSystem(System):
    def run(self, floor):

        for e in floor.components["arrowtrap"]:
            match e.direction:
                case "down":
                    floor.move_tile(e, 0, 1)
                case "up":
                    floor.move_tile(e, 0, -1)
                case "right":
                    floor.move_tile(e, 1, 0)
                case "left":
                    floor.move_tile(e, -1, 0)

            e.tick()

        arrow_tiles = [(tile.x, tile.y) for tile in floor.components["arrowtrap"]]
        for e in floor.components["entities"]:
            if not e.dead:
                if (e.x, e.y) in arrow_tiles:
                    e.health -= 10
                    floor.world.log_message( f"{e.name} got hit by an arrow for {10} damage!" )
        
        for e in floor.components["potion"]:
            if not e.used:
                if (e.x, e.y) in arrow_tiles:
                    e.used =  True

        floor.components["arrowtrap"] = [ e for e in floor.components["arrowtrap"] if e.lifetime > 0 ]


class Floor:
    def __init__(self, world, grid_w, grid_h):
        self.grid = self.create_floor(grid_w, grid_h)

        self.world = world
        self.components = {"entities": []}

        self.systems = [EntitySystem(), ArrowTrapSystem(), PostionSystem()]

        # add some potions to the floor
        for _ in range(3):
            self.add_component("potion", Potion(0, 0, "Potion", "P", (140, 255, 200)))

        for _ in range(3):
            self.add_component("arrowtrap", ArrowTrap("*", 0, 0, (123,123,123), 30))

    def create_floor(self, grid_w, grid_h):
        grid = [["#" for _ in range(grid_w)] for _ in range(grid_h)]
        rooms = []

        room_count = random.randint(7, 20)
        room_min_size = 3
        room_max_size = 5

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
        stair_up_x, stair_up_y = self.find_valid_spawn(grid)
        grid[stair_up_y][stair_up_x] = "<"
        stair_down_x, stair_down_y = self.find_valid_spawn(grid)
        grid[stair_down_y][stair_down_x] = ">"

        return grid

    def is_movable(self, x, y):
        return self.grid[y][x] != "#"

    def move_tile(self, entity, x, y):
        # check for walls and other stuff here
        new_x = entity.x + x
        new_y = entity.y + y

        if not self.is_movable(new_x, new_y):
            return

        entity.x = new_x
        entity.y = new_y

    # kinda want this to be a system, but not sure how yet...
    def move_entity(self, entity, x, y):
        # check for walls and other stuff here
        new_x = entity.x + x
        new_y = entity.y + y

        if not self.is_movable(new_x, new_y):
            return

        for e in self.components["entities"]:
            if e is not entity and e.x == new_x and e.y == new_y:

                # attack seq (entity then other: e)
                # basic attack stuff
                damage = random.randint(1,entity.strength)
                if entity.weapon:
                    damage = random.randint(entity.weapon.min_damage + entity.strength, entity.weapon.max_damage + entity.strength)
                e.health -= damage

                self.world.log_message( f"{entity.name} attacks {e.name} for {damage}!" )
                if e.health <= 0:
                    self.world.log_message(f"{e.name} dies!")
                    e.dead = True
                    entity.experience += e.ex_gain
                    self.world.log_message( f"{entity.name} gains {e.ex_gain} experience!" )
                    entity.score += e.ex_gain
                    if entity.experience >= entity.experience_to_level:
                        entity.level_up()
                        self.world.log_message( f"{entity.name} levels up to level {entity.level}!" )
                        entity.score += 50
                    if entity.health <= 0:
                        self.world.log_message(f"{entity.name} dies!")
                        entity.dead = True
                return

        entity.x = new_x
        entity.y = new_y

    def update(self):
        for system in self.systems:
            system.run(self)


    def add_system(self, system):
        self.systems.append(system)


    def add_component(self, component, value=None):
        has_visual_tag = hasattr(value, "dead") or hasattr(value, "used") or hasattr(value, "visable")
        assert has_visual_tag, "component doesnt have a visual tag"
        if component in self.components:
            if value:
                if hasattr(value, "x") and hasattr(value, "y"):
                    x, y = self.find_valid_spawn(self.grid)
                    value.x = x
                    value.y = y
                    self.components[component].append(value)
                else:
                    self.components[component].append(value)
        else:
            if value:
                if hasattr(value, "x") and hasattr(value, "y"):
                    x, y = self.find_valid_spawn(self.grid)
                    value.x = x
                    value.y = y
                    self.components[component] = [value]
                else:
                    self.components[component] = [value]


    def find_valid_spawn(self, grid):
        height = len(grid)
        width = len(grid[0])
        while True:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if grid[y][x] == ".":
                return (x, y)


    def find_up_stairs(self, grid):
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if grid[y][x] == "<":
                    return (x, y)
        return None


    def find_down_stairs(self, grid):
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if grid[y][x] == ">":
                    return (x, y)
        return None
