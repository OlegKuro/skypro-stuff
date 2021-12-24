from typing import Union

import os


def cls():
    """Clears output: helper"""
    os.system('cls' if os.name == 'nt' else 'clear')


def suppressExceptions(*exceptions):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                pass

        return wrapper

    return decorator


class UnitDied(Exception):
    pass


class UnwalkableException(Exception):
    pass


class Unit:
    def __init__(self, hp, coord):
        self.hp = hp
        self.got_key = False
        self.coord = coord
        self.escaped = False

    def has_key(self):
        return self.got_key

    def set_key(self, val):
        self.got_key = val

    def has_escaped(self):
        return self.escaped

    def set_escaped(self, val=True):
        self.escaped = val

    def get_damage(self, damage):
        if hasattr(self, 'defence'):
            if damage <= self.defence:
                return

        if self.hp - damage <= 0:
            raise UnitDied

        self.hp -= damage

    def set_coordinates(self, x, y):
        self.coord = (x, y)

    def get_coordinates(self):
        return self.coord

    def has_position(self, coord):
        return self.coord == coord


class Ghost(Unit):
    name = 'Ghost'


class Terrain:
    def __init__(self, walkable, terrain, rewalkable=True):
        self.walkable = walkable
        self.terrain = terrain
        self.rewalkable = rewalkable

    def is_walkable(self):
        return self.walkable

    def is_rewalkable(self):
        return self.rewalkable

    def get_terrain(self):
        return self.terrain

    def step_on(self, unit: Unit):
        pass


class Key(Terrain):
    def __init__(self):
        super(Key, self).__init__(True, 'Key', rewalkable=False)

    def step_on(self, unit: Unit):
        unit.set_key(True)


class Door(Terrain):
    def __init__(self):
        super(Door, self).__init__(True, 'Door')

    def step_on(self, unit: Unit):
        if unit.has_key():
            unit.set_escaped()


class Trap(Terrain):
    def __init__(self, damage=1):
        self.damage = damage
        super(Trap, self).__init__(True, 'Trap')

    def step_on(self, unit: Unit):
        unit.get_damage(self.damage)


class TerrainGrass(Terrain):
    def __init__(self):
        super(TerrainGrass, self).__init__(True, 'Grass')


class Wall(Terrain):
    def __init__(self):
        super(Wall, self).__init__(False, 'Wall')

    def step_on(self, unit: Unit):
        raise UnwalkableException()


class Cell:
    def __init__(self, terrain: Terrain, unit=None):
        self.terrain = terrain
        self.unit = unit

    def get_terrain(self) -> Terrain:
        return self.terrain

    def reset_terrain(self, default=None):
        self.terrain = default or TerrainGrass()

    def get_unit(self) -> Union[Unit, None]:
        return self.unit

    def set_unit(self, unit: Unit):
        self.unit = unit

    def _remove_unit(self):
        self.unit = None

    def move_unit_to(self, unit, cell):
        self._remove_unit()
        cell.set_unit(unit)

        if not self.get_terrain().is_rewalkable():
            self.reset_terrain()

    def get_mapping_alias(self) -> str:
        if self.get_unit() is not None:
            return Ghost.name
        return self.get_terrain().terrain


class Field:
    def __init__(self, field: list, unit: Unit, cols: int, rows: int):
        self.field = field
        self.unit = unit
        self.cols = cols
        self.rows = rows

    def cell(self, x, y) -> Cell:
        return self.field[x][y]

    @suppressExceptions(UnwalkableException)
    def _move_to_cell(self, old_coords, new_coords):
        x, y = new_coords
        if not 0 <= x < self.cols or not 0 <= y < self.rows:
            return
        cell = self.cell(x, y)
        old_cell = self.cell(*old_coords)
        terrain = cell.get_terrain()
        terrain.step_on(self.unit)

        self.unit.set_coordinates(x, y)
        old_cell.move_unit_to(unit=self.unit, cell=cell)

    def move_unit_up(self):
        current_coords = self.unit.get_coordinates()
        self._move_to_cell(current_coords, (current_coords[0] - 1, current_coords[1]))

    def move_unit_down(self):
        current_coords = self.unit.get_coordinates()
        self._move_to_cell(current_coords, (current_coords[0] + 1, current_coords[1]))

    def move_unit_right(self):
        current_coords = self.unit.get_coordinates()
        self._move_to_cell(current_coords, (current_coords[0], current_coords[1] + 1))

    def move_unit_left(self):
        current_coords = self.unit.get_coordinates()
        self._move_to_cell(current_coords, (current_coords[0], current_coords[1] - 1))

    def get_field(self):
        return self.field


class GameController:
    mapping = {
        'Wall': '🔲',
        'Grass': '⬜️',
        'Ghost': '👻',
        'Key': '🗝',
        'Door': '🚪',
        'Trap': '💀',
    }

    def __init__(self, hero: Ghost, field: Field):
        self.game_on = True
        self.hero = hero
        self.field = field

    def make_field(self) -> str:
        return '\n'.join([
            ''.join([self.mapping[cell.get_mapping_alias()] for cell in row])
            for row in self.field.get_field()
        ])

    def play(self):
        while self.game_on and not self.hero.has_escaped():
            cls()
            print(self.make_field())
            cmd = input()

            if cmd == 'w':
                self.field.move_unit_up()
            elif cmd == 'a':
                self.field.move_unit_left()
            elif cmd == 's':
                self.field.move_unit_down()
            elif cmd == 'd':
                self.field.move_unit_right()
            elif cmd in ('stop', 'exit'):
                self.game_on = False


if __name__ == '__main__':
    map = iter('WWWWWWWWWWWggGgggggWWgTTTggDgWWKggggTggWWWWWWWWWWW')
    cols = 10
    rows = 5

    field_col = [None for _ in range(0, rows)]
    field = [field_col.copy() for _ in range(0, cols)]
    ghost = None

    for x in range(0, cols):
        for y in range(0, rows):
            cell = next(map)
            if cell == 'W':
                field[x][y] = Cell(Wall())
            elif cell == 'g':
                field[x][y] = Cell(TerrainGrass())
            elif cell == 'T':
                field[x][y] = Cell(Trap())
            elif cell == 'G':
                ghost = Ghost(3, (x, y))
                field[x][y] = Cell(TerrainGrass(), ghost)
            elif cell == 'K':
                field[x][y] = Cell(Key())
            elif cell == 'D':
                field[x][y] = Cell(Door())

    field = Field(field, ghost, cols, rows)
    controller = GameController(ghost, field)
    controller.play()
