from xml.dom import minidom
import re
import os
import struct

CARGO_SIZE = (
    '',
    'S',
    'M',
    'L',
    'XL',
    'ST'
)

SHIELD_MJ = (
    1,
    5,
    25,
    200,
    1000,
    2000
)
SHIELD_TYPE = (
    '1MJ',
    '5MJ',
    '25MJ',
    '200MJ',
    '1GJ',
    '2GJ'
)

LASERS=(
    (1, "IRE"),
    (2, "PAC"),
    (4, "MD"),
    (8, "PRG"),
    (16, "EBC"),
    (32, "FBL"),
    (64, "HEPT"),
    (128, "ID"),
    (256, "PBE"),
    (512, "PBG"),
    (1024, "EMPC"),
    (2048, "CIG"),
    (4096, "IPG"),
    (8192, "ISR"),
    (16384, "MAL"),
    (32768, "FAA"),
    (65536, "CFA"),
    (131072, "PALC"),
    (262144, "PSG"),
    (524288, "SSC"),
    (1048576, "PPC"),
    (2097152, "IC"),
    (4194304, "GC"),
    (8388608, "IBL"),
    (16777216, "PSP"),
    (33554432, "PBC"),
    (67108864, "TBC"),
    (134217728, "FBC"),
    (268435456, "MINING"),
    (268435456, "TRACTOR"),
    (1073741824, "SL1"),
    (1073741824, "SL2"),
    (2147483648, "AKE"),
    (2147483648, "BKE"),
    (2147483648, "GKE"),
    (268435456, "REPAIR"),
    (536870912, "EEMPC"),
    (536870912, "PMAML"),
    (536870912, "PSSC"),
)

BULLET_FLAGS=(
    (1, "PAC"),
    (2, "BEAM"),
    (4, "ZIGZAG"),    # ion disruptor lock/bounce
    (8, "AOE"),
    (0x10, "DISABLE SHIELDS"),  #16
    (0x20, "IGNORE SHIELDS"),    #32
    (0x40, "AMMO"),    #64
    (0x80, "REPAIR"),    #128
    (0x100, "FLAK"),    #256
    (0x200, "REDUCE SPEED"),    #512
    (0x400, "DRAIN WEAPONS"),    #1024
    (0x800, "DOT"),    #2048
    (0x1000, "FRAG"),    #4096
    (0x2000, "CHARGED")    #8192
)

GUN_POSITIONS = {
    0: 'Cockpit',
    1: 'Front',
    2: 'Rear',
    3: 'Left',
    4: 'Right',
    5: 'Top',
    6: 'Bottom'
}

RACE = {
    1: ['argon', 'core'], 2: ['boron', 'core'], 3: ['split', 'core'], 4: ['paranid', 'core'], 5: ['teladi', 'core'],
    6: ['xenon'], 7: ['kha\'ak'], 8: ['pirates'], 9: ['goner'],
    11: ['enemy'], 12: ['neutral'], 13: ['friendly'], 14: ['unknown'],
    17: ['terran', 'atf'], 18: ['terran', 'usc'], 19: ['yaki']
}

########################################################################################################################

from collections import OrderedDict


class BaseObj(object):
    TEMPLATE=[]
    TFILE_PATTERN = re.compile(r'\/\/.*|\/\*.*?\*\/')
    NUMBER_PATTERN = re.compile(r'^(-?\d+)(\.\d+)?$')

    @classmethod
    def parse_file(cls, filename, **kwargs):
        objects = []
        with open(filename, 'r') as openfile:
            filedata = openfile.read().rstrip('\n\r ;')
            data =  cls.TFILE_PATTERN.subn('', filedata.strip())[0].translate(None, '\n\r').split(';')
        version = data.pop(0)
        length = data.pop(0)

        line_nr = 0
        while data:
            obj = cls(data, line_nr, **kwargs)
            objects.append(obj)
            line_nr += 1
        return objects


    def clean(self, **kwargs):
        if self.line:
            self.data['_id']=self.line
        return self.data

    def cfield(self, fieldname):
        return fieldname.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '').replace('#', 'nr').lower()

    def cvalue(self, value):
        res = self.NUMBER_PATTERN.match(value)  # if result: is number, if result[1] is float
        return (float(value) if res.groups()[1] else int(value)) if res else value

    def __init__(self, data, line_nr=None, **kwargs):
        self.offset = 0
        self._data = data
        self.line = line_nr
        self.fieldmap = OrderedDict()
        self.data = self.parse(self.TEMPLATE)
        self.data['line'] = self.line
        self.clean(**kwargs)

    def parse(self, template, depth=0):
        data = OrderedDict()
        for f in template:
            if isinstance(f, dict):
                if f['type'] == 'list-count-value':
                    count = f['count']
                elif f['type'] == 'list-count-field':
                    count_field = self.cfield(f['count_field'])
                    try:
                        count = int(data[count_field])
                    except Exception, e:
                        print '(119) Error %s\ncount field: %s\ndata:' % (e, count_field)
                        print '------------\n{}\n---------'.format(data)
                        raise
                else:
                    raise Exception('unknown struct type: %r' % (f))

                cf = self.cfield(f['field'])
                grp_res = []
                for i in xrange(count):
                    grp_res.append(self.parse(f['fields'], depth+1))
                #data.set_item(cf, grp_res, f['field'])
                data[cf] = grp_res
                self.fieldmap[cf] = f['field']

            elif isinstance(f, str):
                cf = self.cfield(f)
                value = self._data.pop(0).strip()
                #data.set_item(cf, self.cvalue(value), f)
                data[cf] = self.cvalue(value)
                self.fieldmap[cf] = f

            else:
                raise Exception('unknown field type: %r' % (f))

        return data

    def pprint(self, data=None, depth=0):
        if depth==0:
            data = self.data
        elif not data:
            return
        elif isinstance(data, (str, unicode, float, int)):
            print ('  '*depth)+'%s' % (data)
            return

        for f, d in data.items():
            if isinstance(d, dict):
                self.pprint(d, depth+1)
            elif isinstance(d, list):
                print ('  '*depth)+'%s:' % (f)
                for e in d:
                    self.pprint(e, depth+1)
            else:
                print ('  '*depth)+'%s: %s' % (f, d)

    def pprint2(self, data=None, path='', label=''):
        out=[]
        if path=='':
            data = self.data
        elif not data:
            return out
        elif isinstance(data, (str, unicode, float, int)):
            out.append((path, label, data))
            return out

        for f, a in data.items(True):
            l, d = a['label'], a['value']
            if isinstance(d, dict):
                out += self.pprint2(d, '%s/%s' % (path, f), l)
            elif isinstance(d, list):
                for i, e in enumerate(d):
                    r=self.pprint2(e, '%s/%s/%s' % (path, f, i), '%s %d' % (l, i))
                    out += r
            else:
                out.append(('%s/%s' % (path, f), l, d))

        return out


class StreamString(object):
    def __init__(self, s):
        self.s = s
        self.l = len(s)
        self.p = 0
    def skip(self, n):
        self.p += n
        return self
    def read(self, n, peek=False, skip=0):
        if self.l-self.p < n:
            print 'Stream.read, insufficient length', self.l, self.p, n

        nc = self.s[self.p:self.p+n]
        if not peek:
            self.p += n + skip
        return nc
    def readStr(self, peek=False):
        n = self.s.index('\x00', self.p) - self.p
        return self.read(n, peek, 1)
    def __len__(self):
        return self.l - self.p
    def reset(self, pos=0):
        self.p = pos
    def readShort(self, peek=False):
        return struct.unpack('>H', self.read(2, peek=peek))[0]

    def readInt(self, peek=False):
        return struct.unpack('>l', self.read(4, peek=peek))[0]

    def readFloat(self, peek=False):
        return (self.readInt(peek=peek)/65536.0)


class Pages(object):
    def get_pages(self):
        titles={}
        pages=OrderedDict()
        try:
            xmldoc = minidom.parse('ap/addon/t/0001-l044.pck')
        except:
            return OrderedDict()
        for page in xmldoc.getElementsByTagName('page'):
            page_id = int(page.attributes['id'].value) % 300000
            title = page.attributes['title'].value.strip()
            if title in titles:
                page_id = titles[title]
            else:
                titles[title] = page_id
                pages[page_id]=OrderedDict()
                pages[page_id][-1]=title
            for t in page.getElementsByTagName('t'):
                t_id = int(t.attributes['id'].value)
                t_data = t.childNodes[0].data
                pages[page_id][t_id] = t_data
        return pages


    def get_page(self, page, t):
        PAGE_PAT = re.compile(r'\{\d+,\d+\}|\([^)]+?\)|[^(){}]*')
        try:
            raw = self.pages[page][t]
        except:
    #        print 'ERROR trying to get page %d, %d' % (page, t)
            return None
        res = ''
        for e in PAGE_PAT.findall(raw):
            if e.startswith('('):
                pass
            elif e.startswith('{'):
                p1, t1 = map(int, e[1:-1].split(','))
                res += self.get_page(p1, t1)
            else:
                res += e
        return res

    def __init__(self):
        self.pages = self.get_pages()


class Lookups(object):
    def get_lookups(self):
        entries={}
        try:
            xmldoc = minidom.parse('ap/addon/director/dirobjdb.xsd')
        except Exception as e:
            print 'get_lookups error: {}'.format(e)
            return {}
        for entry in xmldoc.getElementsByTagName('xs:enumeration'):
            id = entry.attributes['value'].value.strip()
            name = entry.getElementsByTagName('xs:documentation')[0].childNodes[0].data.strip()
            entries[id] = name
        return entries

    def __init__(self):
        self.lookups = self.get_lookups()

    def __getitem__(self, id):
        return self.lookups[id]

    def __contains__(self, id):
        return id in self.lookups


########################################################################################################################


def walk_files(ext):
    def is_invalid(filename):
        fn = filename.lower()
        return (fn.startswith(('col_', 'turret', 'weapon')) or 'turret' in fn or 'weapon' in fn
                 or 'wreck' in fn or 'door' in fn or 'radar' in fn or 'dummy' in fn or 'fan' in fn
                 or 'gun' in fn or 'barrel' in fn or 'gatling' in fn or 'laser' in fn or 'anim' in fn
                 or 'engine' in fn or 'quicklaunch' in fn or 'disc' in fn or 'destr' in fn)
    l=[]
    for p, sd, fns in list(os.walk('tc/objects/ships'))+list(os.walk('ap/objects/ships'))+list(os.walk('tc/objects/stations'))+list(os.walk('ap/objects/stations')):
        for fn in fns:
            if fn.endswith(ext):
                if is_invalid(fn):
                    continue

                l.append((p, fn))
    return l


def get_file(pathfilename, prepaths=('tc/objects/', 'ap/objects/')):
    import os
    if '/' not in pathfilename:
        print 'no path> '+pathfilename
        return None
    path, filename = pathfilename.rsplit('/', 1)
    lc_filename = filename.lower()

    for pp in prepaths:
        if os.path.isdir(pp + path):
            for fn in os.listdir(pp + path):
                if lc_filename == fn.lower():
                    return pp + path + '/' + fn

    new_path = get_file(path)
    if new_path:
        return get_file(new_path+'/'+filename, prepaths=('',))

    print 'DNE>', pathfilename
    return None


def get_ref_file(ref):
    if isinstance(ref, (str, unicode)):
        scene_filename = ref.replace('\\', '/') + '.pbd'
        return get_file(scene_filename)
    return None

def get_lasers(laser_bits):
    out=[]
    for bit, name in LASERS:
        if bit & laser_bits:
            out.append(name)
    return out


def get_bullet_flags(bullet_bits):
    out=[]
    for bit, name in BULLET_FLAGS:
        if bit & bullet_bits:
            out.append(name)
    return out

########################################################################################################################


if __name__ == '__main__':
    import pymongo
    mongo=pymongo.MongoClient()
    db=mongo.x3

    if 0:
        PAGES=Pages()
        print "Saving pages"
        db.pages.drop()
        for page_id, ts in PAGES.pages.items():
            title = ts.pop(-1)
            for id, data in ts.items():
                db.pages.save(dict(page=page_id, page_title=title, t=id, data=data))
