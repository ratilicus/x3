from x3lib import *


RESOURCE_TYPE = {0: 'ware', 6: 'primary', 7: 'product', 8: 'secondary'}

WARE_CATEGORY = {
    5: ['station', 'dock'], 6: ['station', 'factory'],
    7: ['ship'], 8: ['laser'], 9: ['shield'], 10: ['missile'], 11: ['energy'], 12: ['novelty'],
    13: ['consumable', 'base'], 14: ['consumable', 'food'], 15: ['mineral'], 16: ['tech']
}

ASTEROID_TYPE = {0: 'ore', 1: 'silicon', 2: 'nividium', 3: 'ice'}

GATE_DIR = {0: 'north', 1: 'south', 2: 'west', 3: 'east'}

RACE = {
    1: ['argon', 'core'], 2: ['boron', 'core'], 3: ['split', 'core'], 4: ['paranid', 'core'], 5: ['teladi', 'core'],
    6: ['xenon'], 7: ['kha\'ak'], 8: ['pirates'], 9: ['goner'],
    11: ['enemy'], 12: ['neutral'], 13: ['friendly'], 14: ['unknown'],
    17: ['terran', 'atf'], 18: ['terran', 'usc'], 19: ['yaki']
}


########################################################################################################################


def search_children(xml, fn):
    res=[]
    for n in xml.childNodes:
        if n.nodeType == n.ELEMENT_NODE and fn(n):
            res.append(n)
    return res


def get_station_wares(lookup):
    try:
        xmldoc = minidom.parse('ap/addon/maps/waretemplate.pck')
    except:
        return OrderedDict()
    stations=OrderedDict()
    universe_node = u=xmldoc.getElementsByTagName('universe')[0]
    sector_node = search_children(universe_node, lambda n: int(n.getAttribute('t'))==1)[0]
    for station_node in search_children(sector_node, lambda n: int(n.getAttribute('t')) in (5, 6)):
        station_id = station_node.getAttribute('s')
        if int(station_node.getAttribute('t')) == 5:
            station_type = ['dock']
        elif station_id.endswith('BIG'):
            station_type = ['shipyard', 'big']
        elif station_id.endswith('SHIP'):
            station_type = ['shipyard', 'normal']
        else:
            station_type = ['factory']

        station_wares = []
        for container_node in search_children(station_node, lambda n: int(n.getAttribute('t'))==23):
            container_type = int(container_node.getAttribute('s'))   # 6=primary resource, 7=product, 8=secondary resource
            for ware in search_children(container_node, lambda n: True):
                ware_cat = int(ware.getAttribute('t'))
                ware_id = ware.getAttribute('s')
                station_wares.append(dict(
                    resource=RESOURCE_TYPE[0] if station_type==5 else RESOURCE_TYPE[container_type],
                    category=WARE_CATEGORY[ware_cat],
                    ware=ware_id,
                    name=lookup[ware_id] if ware_id in lookup else None
                ))

        station = dict(
            _id=station_id,
            type=station_type,
            wares=station_wares,
            name=lookup[station_id] if station_id in lookup else None
        )
        stations[station_id] = station
    return stations


def get_gate_type(t):
    if t in (-1, 4):
        return ['destroyed']
    elif t>=9:
        return ['hub']
    else:
        return ['warp' if t<4 else 'trans', GATE_DIR[t % 5]]


def get_sector_objects(lookup, pages, station_types):
    try:
        xmldoc = minidom.parse('ap/addon/maps/x3_universe.pck')
    except:
        return OrderedDict()
    sectors=[]
    universe_node = u=xmldoc.getElementsByTagName('universe')[0]
    for sector_node in search_children(universe_node, lambda n: int(n.getAttribute('t'))==1):
        minerals = dict((v,dict(total=0, yields=[])) for v in ASTEROID_TYPE.values())
        stations = []
        asteroids = []
        gates = []
        for object_node in search_children(sector_node, lambda n: int(n.getAttribute('t')) in (5, 6, 17, 18)):
            object_type = int(object_node.getAttribute('t'))
            object_id = object_node.getAttribute('s')

            if object_type in (5, 6):
                if int(object_node.getAttribute('t')) == 5:
                    object_type = ['dock']
                elif object_id.endswith('BIG'):
                    station_type = ['shipyard', 'big']
                elif object_id.endswith('SHIP'):
                    station_type = ['shipyard', 'normal']
                else:
                    station_type = ['factory']

                station_wares = []
                container_nodes = search_children(object_node, lambda n: int(n.getAttribute('t'))==23)
                for container_node in container_nodes:
                    container_type = int(container_node.getAttribute('s'))   # 6=primary resource, 7=product, 8=secondary resource
                    for ware in search_children(container_node, lambda n: True):
                        ware_cat = int(ware.getAttribute('t'))
                        ware_id = ware.getAttribute('s')
                        station_wares.append(dict(
                            resource=RESOURCE_TYPE[0] if station_type==5 else RESOURCE_TYPE[container_type],
                            category=WARE_CATEGORY[ware_cat],
                            ware=ware_id,
                            name=lookup[ware_id] if ware_id in lookup else None
                        ))
                station = dict(
                    _id=object_id,
                    type=station_type,
                    race=RACE[int(object_node.getAttribute('r'))],
                    wares=station_wares,
                    name=lookup[object_id] if object_id in lookup else None
                )

                if not container_nodes and object_id in station_types:
                    station['wares'] = station_types[object_id]['wares']
                    station['template_wares'] = True

                stations.append(station)

            elif object_type==17:  # Asteroid
                atype = ASTEROID_TYPE[int(object_node.getAttribute('atype'))]
                ayield = int(object_node.getAttribute('aamount'))
                minerals[atype]['total'] += ayield
                minerals[atype]['yields'].append(ayield)
                asteroid = {
                    'x': int(object_node.getAttribute('x')),
                    'y': int(object_node.getAttribute('y')),
                    'z': int(object_node.getAttribute('z')),
                    'type': atype,
                    'yield': ayield
                }
                asteroids.append(asteroid)
            elif object_type==18:  # Gate
                gid=int(object_node.getAttribute('gid'))
                gtid=int(object_node.getAttribute('gtid'))
                gate = dict(
                    x=int(object_node.getAttribute('x')),
                    y=int(object_node.getAttribute('y')),
                    z=int(object_node.getAttribute('z')),
                    type=['gate'] + get_gate_type(int(object_id)),
                    gid=get_gate_type(gid)[-1],
                    gtid=get_gate_type(gtid)[-1],
                    gxid=int(object_node.getAttribute('gxid')) if 0>=gtid>=3 else None,
                    gyid=int(object_node.getAttribute('gyid')) if 0>=gtid>=3 else None,
                )
                gates.append(gate)

        for t in ASTEROID_TYPE.values():
            ct = len(minerals[t]['yields'])
            if ct:
                minerals[t]['yields'].sort(reverse=True)
                minerals[t]['count'] = ct
                minerals[t]['average'] = minerals[t]['total'] / ct
                minerals[t]['median'] = minerals[t]['yields'][ct/2]
                minerals[t]['max'] = minerals[t]['yields'][0]
                minerals[t]['min'] = minerals[t]['yields'][-1]
                minerals[t]['total25plus'] = sum(y for y in minerals[t]['yields'] if y >= 25)
                minerals[t]['yields25plus'] = ','.join(str(y) for y in minerals[t]['yields'] if y >= 25)
                del minerals[t]['yields']
            else:
                del minerals[t]
        x=int(sector_node.getAttribute('x'))
        y=int(sector_node.getAttribute('y'))
        id = 1020101+y*100+x
        sector = dict(
            _id=id,
            x=x,
            y=y,
            race=RACE[int(sector_node.getAttribute('r'))],
            core=bool(sector_node.getAttribute('f')),
            name=pages.get_page(7, id),
            minerals=minerals,
            stations=stations,
            asteroids=asteroids,
            gates=gates,
        )
        sectors.append(sector)
    return sectors


########################################################################################################################


if __name__ == '__main__':
    import pymongo
    mongo=pymongo.MongoClient()
    db=mongo.x3


    if 1:
        print "Getting lookups"
        lookup=Lookups()

        if 1:
            print "Getting station wares"
            stations = get_station_wares(lookup)

            print "Saving station wares", len(stations)
            db.stations.drop()
            for station in stations.values():
                db.stations.save(station)

        if 1:
            print "Getting pages"
            pages=Pages()

            sectors = get_sector_objects(lookup=lookup, pages=pages, station_types=stations)
            print "Saving sector objects", len(sectors)
            db.sectors.drop()
            for sector in sectors:
                db.sectors.save(sector)

