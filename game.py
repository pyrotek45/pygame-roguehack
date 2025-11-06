import pygame
import sys
import random



from enum import Enum, auto
from entities import Entity, create_random_mob, Weapon
from floor import Floor 


pygame.init()


FONTSIZE = 32
GRID_W = 40
GRID_H = 20
LOG_SIZE = 9
TOP_BAR_SIZE = 3


font = pygame.font.SysFont("Consolas", FONTSIZE)
screen = pygame.display.set_mode( ( GRID_W * FONTSIZE, GRID_H * FONTSIZE + (LOG_SIZE * FONTSIZE) + (TOP_BAR_SIZE * FONTSIZE)) )
clock = pygame.time.Clock()


class State(Enum):
    GAMEOVER = auto()
    OVERWORLD = auto()
    HELP = auto()


class World:
    def __init__(self):
        self.state = State.OVERWORLD
        self.player = Entity("player", 5, 5, 100, 5, (0, 255, 0), "@", Weapon("Sword", 30, "!", 5, 10))
        self.floors = [Floor(self, GRID_W, GRID_H)]
        self.current_floor = 0
        self.add_mobs(3)
        self.log = []
        self.map.add_component("entities", self.player)
        
        # Fog of war system
        self.visible_tiles = set()  # Tiles currently visible
        self.seen_tiles = set()  # Tiles that have ever been seen on current floor
        self.vision_radius = 8  # Vision range
        self.floor_seen_tiles = {self.current_floor: self.seen_tiles}
        self.calculate_fov()

    def reset(self):
        self.state = State.OVERWORLD
        self.player = Entity("player", 5, 5, 100, 5, (0, 255, 0), "@", Weapon("Sword", 30, "!", 5, 10))
        self.floors = [Floor(self, GRID_W, GRID_H)]
        self.current_floor = 0
        self.add_mobs(3)
        self.log = []
        self.map.add_component("entities", self.player)
        
        # Reset fog of war
        self.visible_tiles = set()
        self.seen_tiles = set()
        self.floor_seen_tiles = {self.current_floor: self.seen_tiles}
        self.calculate_fov()

    def add_mobs(self, num):
        for _ in range(num):
            mob = create_random_mob()
            self.map.add_component("entities", mob)

    @property
    def map(self):
        return self.floors[self.current_floor]

    def go_down_stairs(self):
        # Store explored tiles for the current floor before leaving
        self.floor_seen_tiles[self.current_floor] = self.seen_tiles

        if self.current_floor == len(self.floors) - 1:
            new_floor = Floor(self, GRID_W, GRID_H)
            # fill with mobs
            for _ in range(random.randint(1, self.current_floor + 4)):

                mob = create_random_mob()
                x, y = new_floor.find_valid_spawn(new_floor.grid)
                mob.x = x
                mob.y = y

                for _ in range(random.randint(self.current_floor, self.current_floor + 3)):
                    mob.level_up()
                    
                mob.set_ex(mob.ex_gain + self.current_floor * 2)

                new_floor.add_component("entities", mob)

            new_floor.add_component("entities", self.player)

            self.floors.append(new_floor)

        self.current_floor += 1
        self.player.x, self.player.y = self.map.find_up_stairs(self.map.grid)
        # Reset fog of war for new floor
        self.visible_tiles = set()
        self.seen_tiles = self.floor_seen_tiles.setdefault(self.current_floor, set())
        self.floor_seen_tiles[self.current_floor] = self.seen_tiles
        self.calculate_fov()

    def go_up_stairs(self):
        # Store explored tiles for the current floor before leaving
        self.floor_seen_tiles[self.current_floor] = self.seen_tiles

        self.current_floor -= 1
        self.player.x, self.player.y = self.map.find_down_stairs(self.map.grid)
        # Reset fog of war for new floor
        self.visible_tiles = set()
        self.seen_tiles = self.floor_seen_tiles.setdefault(self.current_floor, set())
        self.floor_seen_tiles[self.current_floor] = self.seen_tiles
        self.calculate_fov()

    # log can only show 8, so perhaps list needs to erase non visable ones, otherwise
    # list could grow and waste memory. unless there is a log history feature at some point?
    def log_message(self, message):
        self.log.append(message)
        while len(self.log) > 9:
            self.log.pop(0)

    def calculate_fov(self):
        """Calculate field of view using raycasting - walls block vision"""
        self.visible_tiles = set()
        px, py = self.player.x, self.player.y
        
        # Add player position as visible (note: using (y, x) format for consistency)
        self.visible_tiles.add((py, px))
        self.seen_tiles.add((py, px))
        
        # Cast rays to all tiles within vision radius
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(-self.vision_radius, self.vision_radius + 1):
                distance = (dx * dx + dy * dy) ** 0.5
                if distance > self.vision_radius:
                    continue
                
                # Cast ray from player to this tile using Bresenham-like algorithm
                target_x = px + dx
                target_y = py + dy
                
                # Check bounds
                if target_x < 0 or target_x >= GRID_W or target_y < 0 or target_y >= GRID_H:
                    continue
                
                # Cast ray
                x0, y0 = px, py
                x1, y1 = target_x, target_y
                
                # Use integer-based line drawing
                steps = max(abs(x1 - x0), abs(y1 - y0))
                
                if steps == 0:
                    self.visible_tiles.add((y0, x0))  # (y, x) format
                    self.seen_tiles.add((y0, x0))
                    continue
                
                for step in range(steps + 1):
                    if steps > 0:
                        t = step / steps
                        x = int(x0 + (x1 - x0) * t)
                        y = int(y0 + (y1 - y0) * t)
                    else:
                        x, y = x0, y0
                    
                    # Check bounds
                    if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
                        break
                    
                    # Add to visible tiles (before checking if wall) - using (y, x) format
                    self.visible_tiles.add((y, x))
                    self.seen_tiles.add((y, x))
                    
                    # Check if wall blocks vision (stop here, can't see beyond)
                    if self.map.grid[y][x] == "#":
                        break

    def update(self):
        self.map.update()
        
        # Calculate field of view
        self.calculate_fov()
        
        if self.player.health <= 0:
            self.state = State.GAMEOVER

    def draw_overworld(self):
        color = (255, 255, 255)
        under_player = []
        map_overlay = {}
        
        # First pass: collect all overlay items (only visible ones)
        for overlay_name, overlay in self.map.components.items():
            for obj in overlay:
                pos = (obj.y, obj.x)
                
                # Only add to overlay if visible
                if pos not in self.visible_tiles:
                    continue
                
                # this kind of sucks. all items need some sort of visablity
                # attribute but whatever ig. when adding something to the
                # components use one of these attributes. 
                if hasattr(obj, "dead") and not obj.dead:
                    symbol = (obj.symbol, obj.color)
                    if pos not in map_overlay:
                        map_overlay[pos] = symbol
                    elif map_overlay[pos][1] == "@":
                        under_player.append(obj.name)
                    continue
                elif hasattr(obj, "used") and not obj.used:
                    symbol = (obj.symbol, obj.color)
                    if pos not in map_overlay:
                        map_overlay[pos] = symbol
                    elif map_overlay[pos][1] == "@":
                        under_player.append(obj.name)
                    continue
                elif hasattr(obj, "visable") and obj.visable:
                    symbol = (obj.symbol, obj.color)
                    if pos not in map_overlay:
                        map_overlay[pos] = symbol
                    elif map_overlay[pos][1] == "@":
                        under_player.append(obj.name)
                    continue

        height = len(self.map.grid)
        width = len(self.map.grid[0])
        
        if self.map.grid[self.player.y][self.player.x] == "<":
            under_player.append("up stairs")

        if self.map.grid[self.player.y][self.player.x] == ">":
            under_player.append("down stairs")

        def wall_visible(yy, xx):
            if self.map.grid[yy][xx] != "#":
                return False
            # Wall is visible if adjacent to a seen floor tile
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = yy + dy, xx + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if (ny, nx) in self.seen_tiles and self.map.grid[ny][nx] == ".":
                        return True
            return False

        top_bar_size_offset = (TOP_BAR_SIZE) * FONTSIZE
        text = font.render( f"Name: {self.player.name} LVL: {str(self.player.level)} HP: {str(self.player.health)}/{str(self.player.max_health)} EX: {str(self.player.experience)}/{str(self.player.experience_to_level)} Damage: {str( self.player.weapon.min_damage + self.player.strength if self.player.weapon else 0)} - {str(self.player.weapon.max_damage + self.player.strength if self.player.weapon  else self.player.strength)}", True, color, )
        screen.blit(text, (0, 0))
        text = font.render( f"Floor: {self.current_floor} Score: {str(self.player.score)} | Press ? for help", True, color, )
        screen.blit(text, (0, FONTSIZE ))
        things_under_player = " ".join([item for item in under_player])

        if things_under_player:
            text = font.render( things_under_player, True, color, )
            screen.blit(text, (0, FONTSIZE * 2))

        for y, row in enumerate(self.map.grid):
            for x, ch in enumerate(row):
                pos = (y, x)
                is_visible = pos in self.visible_tiles
                is_seen = pos in self.seen_tiles
                
                # If not seen at all, show black
                if not is_seen:
                    text = font.render(" ", True, (0, 0, 0))
                    screen.blit(text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset))
                    continue
                
                # If seen but not visible, show dimmed (fog of war)
                dimmed_color = (80, 80, 80)  # Dark gray for fog of war
                
                if pos in map_overlay:
                    if map_overlay[pos][1] == "@":
                        # Player is always visible
                        text = font.render("@", True, (0, 255, 0))
                        screen.blit( text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset) )
                    else:
                        symbol_color = map_overlay[pos][1] if is_visible else dimmed_color
                        text = font.render( str(map_overlay[pos][0]), True, symbol_color )
                        screen.blit( text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset) )
                else:
                    render_color = color if is_visible else dimmed_color
                    if ch == "#":
                        if wall_visible(y, x):
                            text = font.render("#", True, render_color)
                        else:
                            text = font.render(" ", True, (0, 0, 0))
                    elif ch == "<":
                        if world.current_floor == 0:
                            text = font.render(".", True, render_color)
                        elif world.current_floor >= 1:
                            stair_color = (255, 215, 0) if is_visible else dimmed_color
                            text = font.render("<", True, stair_color)
                    elif ch == ">":
                        stair_color = (255, 215, 0) if is_visible else dimmed_color
                        text = font.render(">", True, stair_color)
                    else:
                        text = font.render(ch, True, render_color)
                    screen.blit( text, (x * FONTSIZE, y * FONTSIZE + top_bar_size_offset) )

        # draw log
        log_start_y = GRID_H * FONTSIZE + top_bar_size_offset
        for i, log_entry in enumerate(self.log[-LOG_SIZE:]):
            text = font.render(log_entry, True, color)
            screen.blit(text, (0, log_start_y + i * FONTSIZE))

        

    def draw_gameover(self):
        # print dead screen
        text = font.render("You died!", True, (255, 0, 0))
        screen.blit( text, (GRID_W * FONTSIZE // 2 - text.get_width() // 2, GRID_H * FONTSIZE // 2), )
        # show restart option
        text = font.render("Press R to restart", True, (255, 255, 255))
        screen.blit( text, ( GRID_W * FONTSIZE // 2 - text.get_width() // 2, GRID_H * FONTSIZE // 2 + FONTSIZE, ), )

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
                        return

                    case pygame.K_COMMA:
                        if self.current_floor > 0 and world.map.grid[self.player.y][self.player.x] == "<" :
                            world.go_up_stairs()
                        return

                    case pygame.K_r:
                        self.reset()
                        return

                    case pygame.K_q:
                        pygame.quit()
                        sys.exit()

                    case pygame.K_SLASH:
                        self.state = State.HELP
                        return

                    case _:
                        return

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
