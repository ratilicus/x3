import re
import collections
from x3lib import get_ref_file

comments_pat=re.compile(r'\/#.*|\/\/.*|\/\*.*?\*\/')
entry_pat=re.compile(r'(\{.+?\})|(P.+?b)')

def parse_scene(filename=None, filedata=None):
    if filename:
        with open(filename, 'r') as f:
            filedata = f.read()
    elif not filedata:
        raise Exception('no filename and no filedata provided')

    entries = []
    entry=collections.OrderedDict()

    for lineU in comments_pat.subn('', filedata.strip())[0].splitlines():
        line = lineU.strip(';\n\r ')
        if line:
            if line.startswith('P'):
                if entry:
                    entries.append(entry)
                entry=collections.OrderedDict()
                for a in map(lambda a: a.strip(), line.split(';')):
                    try:
                        c = a[0]
                    except:
                        print 'E>', line, map(lambda a: a.strip(), line.split(';'))
                        raise
                    if ' ' in a:
                        entry[c] = a[1:].strip()
                entry['P'] = int(entry['P'])
                if 'C' in entry: entry['C'] = int(entry['C'])
                entry['anim'] = []
            elif line.startswith('{'):
                adata = line[1:-1].split(';')
                flags = int(adata.pop(0), 16)
                anim = dict(flags=flags)

                #print line
                #print flags, adata

                if not flags & 0x10:
                    anim['pos'] = dict(
                        x=int(adata.pop(0)),
                        y=int(adata.pop(0)),
                        z=int(adata.pop(0)),
                    )
                    if flags & 0x4000:
                        anim['pos'].update(
                            t=float(adata.pop(0)),
                            c=float(adata.pop(0)),
                            b=float(adata.pop(0)),
                            ef=float(adata.pop(0)),
                            et=float(adata.pop(0)),
                        )
                if flags & 0x2 and not flags & 0x20:
                    anim['rot'] = dict(
                        a=float(adata.pop(0)),
                        x=float(adata.pop(0)),
                        y=float(adata.pop(0)),
                        z=float(adata.pop(0)),
                    )
                    if flags & 0x8000:
                        anim['rot'].update(
                            t=float(adata.pop(0)),
                            c=float(adata.pop(0)),
                            b=float(adata.pop(0)),
                            ef=float(adata.pop(0)),
                            et=float(adata.pop(0)),
                        )
                if flags & 0x8:
                    anim['target'] = dict()
                    if not flags & 0x40: # not same target
                        anim['target'].update(
                            x=int(adata.pop(0)),
                            y=int(adata.pop(0)),
                            z=int(adata.pop(0)),
                        )
                    if not flags & 0x20: # not same rotation
                        anim['target'].update(
                            r=float(adata.pop(0))   # roll
                        )
                    if flags & 0x20000:
                        anim['target'].update(
                            t=float(adata.pop(0)),
                            c=float(adata.pop(0)),
                            b=float(adata.pop(0)),
                            ef=float(adata.pop(0)),
                            et=float(adata.pop(0)),
                        )
                if flags & 0x800 and not flags & 0x1000:
                    anim['fov'] = float(adata.pop(0))

                if flags & 0x200 and not flags & 0x400:
                    anim['color'] = dict(
                        r=float(adata.pop(0)),
                        g=float(adata.pop(0)),
                        b=float(adata.pop(0)),
                    )
                anim['d'] = int(adata.pop(0))
                anim['i'] = int(adata.pop(0))
                entry['anim'].append(anim)
        if entry:
            entries.append(entry)
    return entries


if __name__ == '__main__':

    import os
    import pymongo
    mongo=pymongo.MongoClient()
    db=mongo.x3
    dne=0

    ships = list((ship['ship_scene'], ship['_id']) for ship in db.ships.find({}, {'ship_scene': 1}))
    ships.sort()
    for scene_filename, ship_id in ships:
        if isinstance(scene_filename, (str, unicode)):
            new_filename = get_ref_file(scene_filename)
            if new_filename and os.path.isfile(new_filename):
                print 'OK>', new_filename
                #scene = parse_scene(new_filename)
                #db.ships.update({'_id':ship_id},{'$set': {'scene': scene}})
                pass
            else:
                print 'DNE> %-25s %s' % (ship_id, scene_filename)
                dne += 1

    print 'DNE total: %d of %d' % (dne, len(ships))

    '''
    entries = parse_scene(filedata=testdata)
    for entry in entries:
        #for k,v in entry.items():
        #    print '%s=%s' % (k, v)
        #print
        print dict(entry)
    '''
