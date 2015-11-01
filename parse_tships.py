from x3lib import *
import re

nonplayable = re.compile('ASTRON|PLACEHOLDER|DRONE|ROBOT|SAT|SPACEFLY|TAXI|BIGCIV|TROOPTRAINER|SEC_TRANSPORT|DUMMY|UFO|TURRET|LASER|OWP|HIVEGUARD|THINKER|BEACON|WP|MINE|TL_P|LIFEFORM|MOD_TL')

VARIANTS = {
    0: '',
    1: 'Vanguard',
    2: 'Sentinel',
    3: 'Raider',
    4: 'Hauler',
    5: 'Miner',
    6: 'Super Freighter',
    7: 'Tanker',
    14: 'Tanker XL',
    15: 'Super Freighter XL',
    16: 'Vanguard',
    17: 'Sentinel',
    19: 'Hauler',
    20: '',
}




class CockpitObj(BaseObj):
    TEMPLATE = (
        "Model file",
        "Picture ID",
        "Rotation X",
        "Rotation Y",
        "Rotation Z",
        "Subtype",
        "Description",
        "Model scene",
        "Compatible lasers",
        "Volume",
        "Relative value",
        "Price modifier 1",
        "Price modifier 2",
        "Size",
        "Relative value (player)",
        "Minimum notoriety",
        "Video ID",
        "Skin index",
        "ID",
    )

    def clean(self):
        self.data['_id']=self.line
        self.data['lasers']=get_lasers(self.data['compatible_lasers'])


class ShipObj(BaseObj):
    TEMPLATE = (
        'H|Body file',
        'H|Picture ID',
        'E|Yaw',
        'E|Pitch',
        'E|Roll',
        'D|Class',
        'D|Description',
        'E|Speed',
        'E|Acceleration',
        'H|Engine sound',
        'E|Average reaction delay',
        'H|Engine effect',
        'H|Engine glow effect',
        'E|Reactor output',
        'H|Sound volume min',
        'H|Sound volume max',
        'D|Ship scene',
        'D|Cockpit scene',
        'H|Possible lasers',
        'H|Gun count',
        'E|Weapons energy',
        'E|Weapons recharge',
        'E|Shield type',
        'E|Shield count',
        'E|Possible missiles',
        'E|Number of missiles',
        'E|Engine tunings',
        'E|Rudder tunings',
        'E|Cargo min',
        'E|Cargo max',
        'E|Predefined Wares',
        dict(
            field='H|Cockpit Definitions',
            type='list-count-value',
            count=6,
            fields=(
                'Cockpit index',
                'Cockpit position'
            )
        ),
        'E|Docking slots',
        'E|Cargo type',
        'D|Race',
        'E|Hull strength',
        'H|Explosion definition',
        'H|Body explosion definition',
        'H|Engine Trail',
        'E|Variation index',
        'E|Max Rotation Acceleration',
        'D|Class Description',
        'H|Cockpit Count',
        dict(
            field='H|Cockpits',
            type='list-count-field',
            count_field='Cockpit Count',
            fields=(
                'Index',
                'Turret index',
                'Body ID',
                'Path index'
            )
        ),
        'H|Gun Group Count',
        dict(
            field='H|Gun Groups',
            type='list-count-field',
            count_field='Gun Group Count',
            fields=(
                'Initial laser index',
                'No of guns',
                'Index',
                'No of gun records',
                dict(
                    field='Guns',
                    type='list-count-field',
                    count_field='No of gun records',
                    fields=(
                        'Index',
                        'Count',
                        'Body ID (primary)',
                        'Path index (primary)',
                        'Body ID (secondary)',
                        'Path index (secondary)'
                    )
                )
            )
        ),
        'H|Volume',
        'D|Production RelVal (NPC)',
        'D|Price modifier',
        'D|Price modifier 2',
        'H|Ware class',
        'H|Production RelVal (player)',
        'H|Min. Notoriety',
        'H|Video ID',
        'H|Unknown value',
        'D|ID'
    )

    def clean(self, cockpits, pages):
        o = self
        self.id=o.data['_id']=o.data['id']

        o.data.set_item('playable', not bool(nonplayable.findall(self.id)), 'Playable')
        page_t=o.data['description']
        o.data.set_item('name', pages.get_page(17, page_t), 'Name')
        o.data.set_item('desc', pages.get_page(17, page_t+1), 'Description')

        stype = [o.data['class'].split('_')[2]]
        if stype==['TS'] and self.id.endswith('_TSP'):
            stype.append('TS+')
        elif stype==['M3'] and self.id.endswith('_M3P'):
            stype.append('M3+')
        elif stype==['M6'] and self.id.endswith('_M6M'):
            stype.append('M6+')
        elif stype==['M7']:
            if self.id.endswith('_DC'):
                stype.append('DC')
            elif self.id.endswith(('_M7M', '_HCF')):
                stype.append('M7M')
        elif stype==['M2'] and self.id.endswith('_M2P'):
            stype.append('M2+')

        o.data.set_item('type', stype, 'Type')

        speed = o.data['speed']
        accel = o.data['acceleration']
        turn = max(o.data['pitch'], o.data['yaw'])
        etunes = o.data['engine_tunnings']
        rtunes = o.data['rudder_tunnings']

        o.data['info'] = OrderedDict(
            speed=OrderedDict(min=round(speed/500, 1), max=round(speed*(1.0+0.1*etunes)/500, 1), tunes=etunes),
            accel=OrderedDict(min=round(accel/500, 1), max=round(accel*(1.0+0.1*etunes)/500, 1), tunes=etunes),
            turn=OrderedDict(min=round(turn*60, 2), max=round(turn*(1.0+0.1*rtunes)*60, 2), tunes=rtunes),
            cargo=OrderedDict(min=o.data['cargo_min'], max=o.data['cargo_max'], size=CARGO_SIZE[o.data['cargo_type']]),
            shields=OrderedDict(energy=o.data['shield_count']*SHIELD_MJ[o.data['shield_type']], reactor=o.data['reactor_output'], desc='%dx%s' % (o.data['shield_count'], SHIELD_TYPE[o.data['shield_type']])),
            docking_slots=o.data['docking_slots'],
            weapons=OrderedDict(energy=o.data['weapons_energy'], recharge=round(o.data['weapons_energy']*o.data['weapons_recharge'])),
            race=RACE[o.data['race']]
        )

        cockpit_lasers=get_lasers(o.data['possible_lasers'])
        turrets=[]
        for i, ggd in enumerate(o.data['gun_groups']):
            if i==0:
                cockpit_index=None
                position_index = 0
                laser_bits = o.data['possible_lasers']
                lasers = cockpit_lasers
            else:
                cpd=o.data['cockpit_definitions'][i-1]
                position_index = cpd['cockpit_position']
                cockpit_index=cpd['cockpit_index']
                cpde=cockpits[cockpit_index].data
                laser_bits=cpde['compatible_lasers']
                lasers=cpde['lasers']

            try:
                cp=o.data['cockpits'][i]
            except:
                cp=OrderedDict()

            if cockpit_index is not None:
                cp['cockpit_index'] = cockpit_index

            if cp:
                cp.pop('index')
                if cp.pop('turret_index') == -1:
                    cp['special'] = True

            cp['position_index'] = position_index
            cp['position']=GUN_POSITIONS[position_index]

            guns=[]
            for g in ggd['guns']:
                g.pop('index')
                guns.append(g)

            gg=OrderedDict(
                cockpit=cp,
                laser_bits=laser_bits,
                laser_types=lasers,
                guns=guns
            )
            turrets.append(gg)
#        print turrets
        o.data['turrets']=turrets
        o.data.pop('cockpit_definitions')
        o.data.pop('cockpits')
        o.data.pop('gun_groups')


########################################################################################################################

if __name__=='__main__':
    print "Getting pages"
    pages=Pages()

    print "Getting cockpits"
    filename = 'ap/addon/types/tcockpits.pck'
    cockpits = CockpitObj.parse_file(filename)

    print "Getting ships"
    filename = 'ap/addon/types/tships.pck'
    ships = ShipObj.parse_file(filename, cockpits=cockpits, pages=pages)

    if 0:  # write to db
        import pymongo
        mongo=pymongo.MongoClient()
        db=mongo.x3

        db.ships.drop()
        for i, o in enumerate(ships):
            shipyards=[]
            for sector in db.sectors.find({'stations.wares.ware': o.id}, {'name':1,'x':1,'y':1,'stations.$':1}):
                shipyards.append('%s [%d, %d] - %s' % (sector['name'], sector['x'], sector['y'], sector['stations'][0]['name']))
            if len(shipyards):
                o.data['shipyards'] = shipyards
    #        print 'adding %3d %s' % (i, o.id)
            db.ships.save(o.data, safe=True)
    #    ships[0].pprint()