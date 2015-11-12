from base import Model, IntField, FloatField, StringField, ListField

class CockpitDefinition(Model):
    index = IntField('Cockpit index')
    position = IntField('Cockpit position')

    def __repr__(self):
        return '<{}>({})'.format(self.__class__.__name__, self.index)


class Cockpit(Model):
    index = IntField('Index')
    turret_index = IntField('Turret index')
    body_id = StringField('Body ID')
    path_index = IntField('Path Index')

    def __repr__(self):
        return '<{}>({})'.format(self.__class__.__name__, self.index)

class Gun(Model):
    index = IntField('Index')
    count = IntField('Count')
    body_id_pri = StringField('Body ID (primary)')
    path_index_pri = IntField('Path Index (primary)')
    body_id_sec = StringField('Body ID (secondary)')
    path_index_sec = IntField('Path Index (secondary)')

    def __repr__(self):
        return '<{}>({})'.format(self.__class__.__name__, self.index)

class GunGroup(Model):
    initial_index = IntField('Initial laser index')
    gun_count = IntField('No of guns')
    index = IntField('Index')
    record_count = IntField('No of gun records')
    guns = ListField(Gun, 'Guns', count_field='record_count')

    def __repr__(self):
        return '<{}>({})'.format(self.__class__.__name__, self.index)

class TShips(Model):
    body_file = StringField('Body file')
    picture_id = StringField('Picture ID')
    yaw = FloatField('Yaw')
    pitch = FloatField('Pitch')
    roll = FloatField('Roll')
    ship_class = StringField('Class')
    description = StringField('Description')
    speed = IntField('Speed')
    acceleration = IntField('Acceleration')
    engine_sound = IntField('Engine sound')
    reaction_delay = IntField('Average reaction delay')
    engine_effect = IntField('Engine effect')
    engine_glow = IntField('Engine glow effect')
    reactor = IntField('Reactor output')
    sound_min = IntField('Sound volume min')
    sound_max = IntField('Sound volume max')
    ship_scene = StringField('Ship scene')
    cockpit_scene = StringField('Cockpit scene')
    lasers = IntField('Possible Lasers')
    gun_count = IntField('Gun count')
    weapons_energy = IntField('Weapons energy')
    weapons_recharge = FloatField('Weapons recharge')
    shield_type = IntField('Shield type')
    shield_count = IntField('Shield count')
    missiles = IntField('Possible missiles')
    missile_count = IntField('Number of missiles')
    engine_tunings = IntField('Engine tunings')
    rudder_tunings = IntField('Rudder tunnings')
    cargo_min = IntField('Cargo min')
    cargo_max = IntField('Cargo max')
    wares = IntField('Predefined wares')
    cockpit_definitions = ListField(CockpitDefinition, 'Cockpit Definitions', count=6)
    docks = IntField('Docking slots')
    cargo_type = IntField('Cargo type')
    race = IntField('Race')
    hull = IntField('Hull strength')
    explosion = IntField('Explosion definition')
    body_explosion = IntField('Body explosion definition')
    trail = IntField('Engine trail')
    variation = IntField('Variation index')
    rotation_accel = IntField('Max Rotation Acceleration')
    class_desc = StringField('Class description')
    cockpit_count = IntField('Cockpit Count')
    cockpits = ListField(Cockpit, 'Cockpit Definitions', count_field='cockpit_count')
    gun_group_count = IntField('Gun Group Count')
    gun_groups = ListField(GunGroup, 'Gun Groups', count_field='gun_group_count')
    volume = IntField('Volume')
    relval_npc = IntField('Production RelVal (NPC)')
    price_mod = IntField('Price modifier')
    price_mod_2 = IntField('Price modifier')
    ware_class = IntField('Ware class')
    relval_player = IntField('Production RelVal (player)')
    notoriety = IntField('Min. Notoriety')
    video_id = IntField('Video ID')
    unknown = StringField('Unknown value')
    id = StringField('ID')

    def __repr__(self):
        return '<{}>({})'.format(self.__class__.__name__, self.id)


import re
from collections import OrderedDict
TFILE_PATTERN = re.compile(r'\/\/.*|\/\*.*?\*\/')

def parse_file(filename):
    objects = []
    with open(filename, 'r') as openfile:
        filedata = openfile.read().rstrip('\n\r ;')
        data =  TFILE_PATTERN.subn('', filedata.strip())[0].translate(None, '\n\r').split(';')
    version = data.pop(0)
    length = data.pop(0)
    return version, length, data


if __name__ == '__main__':
    v, l, data = parse_file('ap/addon/types/tships.pck')

    print len(data)
    ships = OrderedDict()
    while data:
        ship = TShips(data)
        ships[ship.id] = ship
        print '{:30} {:20} {}'.format(ship.id, ship.ship_class, ship.speed)
    print len(data)
    

