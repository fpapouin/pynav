import struct
import json
from typing import List
from dataclasses import dataclass, field, is_dataclass, asdict


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)

# region dataclass


@dataclass
class vector:
    x: float
    y: float
    z: float


@dataclass
class connection:
    source_area: int = 0
    target_area_id: int = 0
    target_area: int = 0
    direction: str = ''


@dataclass
class hiding_spot:
    id: int = 0
    location: vector = vector(0, 0, 0)
    flags: int = 0


@dataclass
class encounter_spot:
    order_id: int = 0
    parametric_distance: float = 0


@dataclass
class encounter_path:
    from_area_id: int = 0
    from_area: int = 0
    from_direction: int = 0
    to_area_id: int = 0
    to_area: int = 0
    to_direction: int = 0
    spots: List[encounter_spot] = field(default_factory=list)


@dataclass
class ladder_connection:
    source_area: int = 0
    target_id: int = 0
    target_ladder: int = 0
    direction: int = 0


@dataclass
class ladder:
    id: int = 0
    width: float = 0
    length: float = 0
    top: vector = vector(0, 0, 0)
    bottom: vector = vector(0, 0, 0)
    direction: int = 0
    top_forward_area_id: int = 0
    top_forward_area: int = 0
    top_left_area_id: int = 0
    top_left_area: int = 0
    top_right_area_id: int = 0
    top_right_area: int = 0
    top_behind_area_id: int = 0
    top_behind_area: int = 0
    bottom_area_id: int = 0
    bottom_area: int = 0


@dataclass
class visible_areas:
    visible_area_id: int = 0
    visible_area: int = 0
    attributes: int = 0


@dataclass
class area:
    id: int = 0
    flags: int = 0
    north_west: vector = vector(0, 0, 0)
    south_east: vector = vector(0, 0, 0)
    north_east_z: float = 0
    south_west_z: float = 0
    connections: List[connection] = field(default_factory=list)
    hiding_spots: List[hiding_spot] = field(default_factory=list)
    encounter_paths: List[encounter_path] = field(default_factory=list)
    place_id: int = 0
    ladder_connections: List[ladder_connection] = field(default_factory=list)
    earliest_occupy_time_first_team: float = 0
    earliest_occupy_time_second_team: float = 0
    north_west_light_intensity: float = 0
    north_east_light_intensity: float = 0
    south_east_light_intensity: float = 0
    south_west_light_intensity: float = 0
    nav_visible_areas: List[visible_areas] = field(default_factory=list)
    inherit_visibility_from_area_id: int = 0


@dataclass
class place:
    id: int
    name: str
    areas: List[area]


@dataclass
class header:
    feedface: int = 0
    version: int = 0
    subversion: int = 0
    bsp_size: int = 0
    place_count: int = 0  # byte 16
    places: List[place] = field(default_factory=list)
    has_unnamed_areas: bool = False
    area_count: int = 0
    ladders: List[ladder] = field(default_factory=list)
# endregion


class Nav:
    buffer: bytes = None

    def __init__(self, filename: str):
        with open(filename, 'rb') as f:
            self.buffer = bytes(f.read())

    def r(self, add: int, size: int):
        return self.buffer[add:add+size]

    def rb(self, add: int):
        return struct.unpack('<B', self.r(add, 1))[0]

    def rus(self, add: int):
        return struct.unpack('<H', self.r(add, 2))[0]

    def ri(self, add: int):
        return struct.unpack('<i', self.r(add, 4))[0]

    def rui(self, add: int):
        return struct.unpack('<I', self.r(add, 4))[0]

    def rf(self, add: int):
        return struct.unpack('<f', self.r(add, 4))[0]

    def rfs(self, add: int, count: int):
        return struct.unpack(f'<{count}f', self.r(add, 4 * count))

    def rs(self, add: int, lenght: int):
        if lenght == 0:
            return b''
        return struct.unpack(f'<{lenght}s', self.r(add, lenght))[0]

    def rsc(self, add: int):
        lenght = 0
        while self.rb(add+lenght) != 0:
            lenght += 1
        return self.rs(add, lenght).decode()


def parse(mapname):
    n = Nav(f'{mapname}.nav')

    d = {}
    d['feedface'] = 0x00
    d['version'] = 0x04
    d['subversion'] = 0x08
    d['bsp_size'] = 0x0C
    d['place_count'] = 0x11

    hd = header()
    hd.feedface = n.rui(d['feedface'])
    hd.version = n.rui(d['version'])
    hd.subversion = n.rui(d['subversion'])
    hd.bsp_size = n.rui(d['bsp_size'])
    hd.place_count = n.rus(d['place_count'])
    printd(f'{hex(hd.feedface)=}')
    printd(f'{hd.version=}')
    printd(f'{hd.subversion=}')
    printd(f'{hd.bsp_size=}')
    printd(f'{hd.place_count=}')

    printd('Get places')
    add = d['place_count'] + 0x02
    for i in range(hd.place_count):
        name_lenght = n.rus(add)
        add += 0x02
        name = n.rsc(add)
        add += name_lenght
        hd.places.append(place(i+1, name, []))
    hd.has_unnamed_areas = n.rb(add) > 0
    printd(f'{hd.has_unnamed_areas=}')
    add += 0x01
    hd.area_count = n.rui(add)
    add += 0x04
    printd(f'{hd.area_count=} {hex(hd.area_count)} ')

    for i in range(hd.area_count):
        a = area()
        a.id = n.rui(add)
        add += 0x04
        a.flags = n.rui(add)
        add += 0x04
        v = n.rfs(add, 3)
        a.north_west = vector(v[0], v[1], v[2])
        add += 3*0x04
        v = n.rfs(add, 3)
        a.south_east = vector(v[0], v[1], v[2])
        add += 3*0x04
        a.north_east_z = n.rf(add)
        add += 0x04
        a.south_west_z = n.rf(add)
        add += 0x04

        for j in ['NavDirectionNorth', 'NavDirectionEast', 'NavDirectionSouth', 'NavDirectionWest']:
            connection_count = n.rui(add)
            add += 0x04
            printd(f'        {connection_count=}')
            for h in range(connection_count):
                c = connection()
                c.source_area = a.id
                c.target_area_id = n.rui(add)
                add += 0x04
                c.target_area = c.target_area_id
                c.direction = j
                a.connections.append(c)

        hiding_spot_count = n.rb(add)
        add += 0x01
        printd(f'    {hiding_spot_count=}')
        for j in range(hiding_spot_count):
            h = hiding_spot()
            h.id = n.rui(add)
            add += 0x04
            v = n.rfs(add, 3)
            h.location = vector(v[0], v[1], v[2])
            add += 3*0x04
            h.flags = n.rb(add)
            add += 0x01
            a.hiding_spots.append(h)

        encounter_path_count = n.rui(add)
        add += 0x04
        printd(f'    {encounter_path_count=}')
        for j in range(encounter_path_count):
            e = encounter_path()
            e.from_area_id = n.rui(add)
            add += 0x04
            e.from_area = e.from_area_id
            e.from_direction = n.rb(add)
            add += 0x01
            e.from_direction = ['NavDirectionNorth', 'NavDirectionEast', 'NavDirectionSouth', 'NavDirectionWest'][e.from_direction]
            e.to_area_id = n.rui(add)
            add += 0x04
            e.to_area = e.to_area_id
            e.to_direction = n.rb(add)
            add += 0x01
            e.to_direction = ['NavDirectionNorth', 'NavDirectionEast', 'NavDirectionSouth', 'NavDirectionWest'][e.to_direction]
            spot_count = n.rb(add)
            add += 0x01
            printd(f'        {spot_count=}')
            for h in range(spot_count):
                s = encounter_spot()
                s.order_id = n.rui(add)
                add += 0x04
                distance = n.rb(add)
                add += 0x01
                s.parametric_distance = distance/255
                e.spots.append(s)
            a.encounter_paths.append(e)

        place_id = n.rus(add)
        add += 0x02
        printd(f'    {place_id=}')
        for p in hd.places:
            if p.id == place_id:
                p.areas.append(a)
                place_id = 0
            if place_id == 0:
                break
        if place_id != 0:
            exit(-1)

        for j in ['NavLadderDirectionUp', 'NavLadderDirectionDown']:
            ladder_connection_count = n.rui(add)
            add += 0x04
            printd(f'        {ladder_connection_count=}')
            for h in range(ladder_connection_count):
                l = ladder_connection()
                l.source_area = a.id
                l.direction = j
                l.target_id = n.rui(add)
                add += 0x04
                a.ladder_connections.append(l)

        a.earliest_occupy_time_first_team = n.rf(add)
        add += 0x04
        a.earliest_occupy_time_second_team = n.rf(add)
        add += 0x04
        a.north_west_light_intensity = n.rf(add)
        add += 0x04
        a.north_east_light_intensity = n.rf(add)
        add += 0x04
        a.south_east_light_intensity = n.rf(add)
        add += 0x04
        a.south_west_light_intensity = n.rf(add)
        add += 0x04

        visible_area_count = n.rui(add)
        add += 0x04
        printd(f'    {visible_area_count=}')
        for j in range(visible_area_count):
            v = visible_areas()
            v.visible_area_id = n.rui(add)
            add += 0x04
            v.attributes = n.b(add)
            add += 0x01
            a.nav_visible_areas.append(v)
        a.inherit_visibility_from_area_id = n.rui(add)
        add += 0x04

        garbage_count = n.rb(add)
        add += 0x01
        printd(f'    {garbage_count=}')
        add += garbage_count*14

    ladder_count = n.rui(add)
    add += 0x04
    printd(f'{ladder_count=}')
    for i in range(ladder_count):
        l = ladder()
        l.id = n.rui(add)
        add += 0x04
        l.width = n.rf(add)
        add += 0x04
        v = n.rfs(add, 3)
        l.top = vector(v[0], v[1], v[2])
        add += 3*0x04
        v = n.rfs(add, 3)
        l.bottom = vector(v[0], v[1], v[2])
        add += 3*0x04
        l.length = n.rf(add)
        add += 0x04
        l.direction = n.rb(add)
        add += 0x04 # not 0x01 for ladder
        l.direction = ['NavLadderDirectionUp', 'NavLadderDirectionDown', 'NavLadderDirectionMax', 'NavLadderDirectionMax'][l.direction]

        l.top_forward_area_id = n.rui(add)
        add += 0x04
        l.top_forward_area = l.top_forward_area_id

        l.top_left_area_id = n.rui(add)
        add += 0x04
        l.top_left_area = l.top_left_area_id

        l.top_right_area_id = n.rui(add)
        add += 0x04
        l.top_right_area = l.top_right_area_id

        l.top_behind_area_id = n.rui(add)
        add += 0x04
        l.top_behind_area = l.top_behind_area_id

        l.bottom_area_id = n.rui(add)
        add += 0x04
        l.bottom_area = l.bottom_area_id
        hd.ladders.append(l)

    with open(f'{mapname}.json', 'w') as text_file:
        result = json.dumps(hd, indent=4, cls=EnhancedJSONEncoder)
        print(result, file=text_file)

def printd(s):
    # print(s)
    pass



def main():
    import os
    import glob
    import shutil
    nav_path = os.path.join(r'C:\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\maps', '*.nav')
    for f in glob.glob(nav_path):
        basename = os.path.basename(f)
        if os.path.isfile(basename):
            os.remove(basename)
        shutil.copy(f, '.')
        basename = basename.replace('.nav', '')
        parse(basename)
    exit(0)


if __name__ == '__main__':
    main()
