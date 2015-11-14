import struct
import os
from x3lib import walk_files, StreamString as Stream


class vec(list):
    def __init__(self, x=None, y=None, z=None):
        self.append(x)
        self.append(y)
        self.append(z)
    x = property(lambda self: self[0])
    y = property(lambda self: self[1])
    z = property(lambda self: self[2])
    u = property(lambda self: self[0])
    v = property(lambda self: self[1])


class vert(object):
    def __init__(self, p, n, t):
        self.p = p
        self.n = n
        self.t = t
    def scaled(self, scale):
        for v in self.p:
            yield v*scale/6553.6


class face(object):
    def __init__(self, tex_idx, v0, v1, v2):
        self.t = tex_idx
        self.v = [v0, v1, v2]


class lod(object):
    def __init__(self, size, flags, mats, verts, faces):
        self.size = size
        self.scale = size/65536.0
        self.flags = flags
        self.mats = mats
        self.verts = verts
        self.faces = faces

    def save_obj(self, fn):
        v_lines = []
        vn_lines = []
        f_lines = []
        for i, v in enumerate(self.verts, start=1):
            v_lines.append('v %0.6f %0.6f %0.6f' % tuple(v.scaled(self.scale)))
            vn_lines.append('vn %0.6f %0.6f %0.6f' % tuple(v.n))
        for i, f in enumerate(self.faces, start=1):
#            f_lines.append('f {f.v[0]}/{f.t}/{f.v[0]} {f.v[1]}/{f.t}/{f.v[1]} {f.v[2]}/{f.t}/{f.v[2]}'.format(f=f))
            f_lines.append('f {f.v[0]}//{f.v[0]} {f.v[1]}//{f.v[1]} {f.v[2]}//{f.v[2]}'.format(f=f))
        lines = v_lines+vn_lines+['s off'] + f_lines

        with open(fn, 'w') as f:
            f.write('\n'.join(lines))

    def thumb(self, fn):
        import Image,ImageDraw

        img = Image.new("RGB", (900,315), "#FFFFFF")
        draw = ImageDraw.Draw(img)
        colors = [(((i*64621)**2) % 256, (((i*12415)**4) % 256), (((i*834793)*3) % 256)) for i in xrange(64)]

        DIVIDER = 65536.0 / 150.0

        for c in xrange(0, 900/150*5):
            i = c*(150.0/5)
            draw.line([i,0,i,300], fill=(192,192,192))

        for c in xrange(0, 300/150*5):
            i = c*(150.0/5)
            draw.line([0, i,900,i], fill=(192,192,192))

        draw.line([0,150,900,150], fill=(0,0,0))
        draw.line([150,0,150,300], fill=(0,0,0))
        draw.line([450,0,450,300], fill=(0,0,0))
        draw.line([750,0,750,300], fill=(0,0,0))

        draw.line([300,0,300,300], fill=(255,255,255))
        draw.line([600,0,600,300], fill=(255,255,255))

        extents = [[0, 0, 0],[0, 0, 0],[0, 0, 0]]

        for f in self.faces:
            verts = [self.verts[vi-1] for vi in f.v]
            try:
                color = colors[f.t]
            except:
                print f.t
                raise

            for v in verts:
                extents[0][0] = min(extents[0][0], v.p.x)
                extents[0][1] = max(extents[0][1], v.p.x)
                extents[1][0] = min(extents[1][0], v.p.y)
                extents[1][1] = max(extents[1][1], v.p.y)
                extents[2][0] = min(extents[2][0], v.p.z)
                extents[2][1] = max(extents[2][1], v.p.z)

            pos=[(150+int(v.p.x/DIVIDER), 150-int(v.p.y/DIVIDER)) for v in verts]
            draw.polygon(pos, fill=color)

            pos=[(450+int(v.p.x/DIVIDER), 150+int(v.p.z/DIVIDER)) for v in verts]
            draw.polygon(pos, fill=color)

            pos=[(750-int(v.p.y/DIVIDER), 150+int(v.p.z/DIVIDER)) for v in verts]
            draw.polygon(pos, fill=color)

        extents[0][2] = extents[0][1] - extents[0][0]
        extents[1][2] = extents[1][1] - extents[1][0]
        extents[2][2] = extents[2][1] - extents[2][0]


        s = 'SIZE: %0.1fm x %0.1fm x %0.1fm' % (
            extents[0][2]*self.scale/500.0,
            extents[1][2]*self.scale/500.0,
            extents[2][2]*self.scale/500.0
        )
        s+= ' | SQR SIZE: %d (%0.1fm)' % (65536.0/5*self.scale, 65536.0/5*self.scale/500.0)
        draw.text((3,303), s, fill=(0,0,0))

        try:
            os.makedirs(os.path.dirname(fn))
        except:
            pass

        img.save(fn, "GIF")
        return (
            round(extents[0][2]*self.scale/500.0, 1),
            round(extents[1][2]*self.scale/500.0, 1),
            round(extents[2][2]*self.scale/500.0, 1)
        )


class Material(object):
    _fields = ('version', 'index', 'texture', 'ambiend', 'diffuse', 'specular', 'transparency', 'self_illumination', 'shininess', 'dest_blend', 'two_sided', 'wire_frame', 'texture_value', 'environment_map', 'light_map', 'flags', 'technique', 'shader_name')
    def __init__(self):
        for f in self._fields:
            setattr(self, f, None)
        self.big = None
        self.small = None
        self.values = []
    class Value(object):
        _fields = ('name', 'value')
        name = None
        value = None
        def __str__(self):
            return 'Value:%s=%s' % (self.name, self.value)

    def p(self, indent=0, label=''):
        indent2 = indent+1
        out=[]
        out.append('\t'*indent+'Material:'+label)
        for f in self._fields:
            v = getattr(self, f)
            if v is None:
                continue

            out.append('\t'*indent2+'%s=%s' % (f, v))
        for v in self.values:
            out.append('\t'*indent2+str(v))

        if self.big:
            out.append(self.big.p(indent2, 'Big'))
        elif self.small:
            out.append(self.small.p(indent2, 'Small'))

        return '\n'.join(out)


########################################################################################################################


def load_tex_pair(s, v):
    if v==6:
        return (s.readStr(), s.readShort())
    else:
        return (str(s.readShort()), s.readShort())


def load_mat5(s, m, flags):
    m.index = s.readShort()
    if m.version==6:
        m.texture = s.readStr()
    else:
        m.texture = str(s.readShort())
        m.ambient = (s.readShort(), s.readShort(), s.readShort())
        m.diffuse = (s.readShort(), s.readShort(), s.readShort())
        m.specular = (s.readShort(), s.readShort(), s.readShort())

    m.transparency = s.readInt()
    m.self_illumination = s.readShort()
    m.shininess = (s.readShort(), s.readShort())

    if m.version!=6:
        flags = s.readShort()

    m.dest_blend = flags & 0x2 > 0
    m.two_sided = flags & 0x10 > 0
    m.wire_frame = flags & 0x8 > 0

    m.texture_value = s.readShort()
    m.environment_map = load_tex_pair(s, m.version)

    m.light_map = load_tex_pair(s, m.version)


def get_lods(fdata, max_lod=16, load_mesh=True, load_mats=False):
    info = (fdata[fdata.index('INFO', 0) + 4: fdata.index('/INF', 0)])
    #print 'INFO', info
    if load_mats:
        mat_start = fdata.index('MAT', 0)
        mat_end = fdata.index('/MAT', mat_start)
        data = Stream(fdata[mat_start: mat_end])
        mat_str = data.read(4)
        if mat_str == 'MAT5' or mat_str == 'MAT6':
            mat_ct = data.readInt()
            print 'MAT>', mat_str, mat_ct
            for i in xrange(mat_ct):
                m = Material()
                m.version = 5 if (mat_str == 'MAT5') else 6
                if m.version==5:
                    load_mat5(data, m, 0)
                else:
                    # load mat6
                    m.index = data.readShort()
                    m.flags = data.readInt()
                    if m.flags & 0x2000000:
                        # big Mat
                        m.big = Material()
                        m.big.technique = data.readShort()
                        m.big.shader_name = data.readStr()
                        m.big.values = []
                        value_ct = data.readShort()
                        for c in xrange(value_ct):
                            v = Material.Value()
                            v.name = data.readStr()
                            v_type = data.readShort()
                            if v_type == 0:
                                v.value = data.readInt()
                            elif v_type == 1:
                                v.value = data.readInt() != 0
                            elif v_type == 8:
                                v.value = data.readStr()
                            elif v_type == 2:
                                v.value = data.readFloat()
                            elif 3<=v_type<=5:
                                v.value = tuple(data.readFloat() for i in xrange(v_type-1))
                            m.big.values.append(v)
                    else:
                        # Small Mat
                        s.skip(-2)
                        m.small = Material()
                        load_mat5(data, m.small, m.flags)
                #print m.p()
                mats.append(m)
        else:
#            print 'INVALID MAT TYPE>', mat_str
            pass

    body_index = fdata.index('BODY')+4
    data = Stream(fdata[body_index: body_index+4])
    mesh_count = min(max_lod, data.readShort())
    lods = []
    start_index = body_index
    for i0 in xrange(mesh_count):
        min_ind_idx=100000
        max_ind_idx=-1
        max_tex_idx=0
        mats=[]
        verts=[]
        faces=[]

        verts_start = fdata.index('POIN', start_index) + 4
        verts_end = fdata.index('/POI', verts_start)
        face_start = fdata.index('PART', verts_end) + 4
        face_end = fdata.index('/PAR', face_start)
        start_index = face_end + 4

        data = Stream(fdata[verts_start-12: verts_start-4])
        lod_size = data.readInt()
        lod_flags = data.readInt()

        if load_mesh:
            data = Stream(fdata[verts_start: verts_end])
            vert_ct = data.readInt()
            for i in xrange(vert_ct):
                flags = data.readShort()
                if flags & 0x19 != 0x19:
                    print 'bad vec', i, flags
                    continue
                pos = vec(data.readInt(), data.readInt(), data.readInt())

                if flags & 0x2:
                    texcoord = vec(data.readFloat(), data.readFloat())
                if flags & 0x4:
                    st = vec(data.readFloat(), data.readFloat())

                normal = vec(data.readFloat(), data.readFloat(), data.readFloat())
                sg = data.readInt()
                verts.append(vert(pos, normal, texcoord))

            data = Stream(fdata[face_start: face_end])

            facegroup_ct = data.readInt()
            for i in xrange(facegroup_ct):
                flags = data.readInt()
                texgroup_ct = data.readShort()
                for j in xrange(texgroup_ct):
                    mat_idx = data.readInt()
                    indices_ct = data.readInt()
                    for k in xrange(indices_ct):
                        f = face(mat_idx, data.readInt()+1, data.readInt()+1, data.readInt()+1)
                        faces.append(f)
                        data.readInt() # ? part of indices
                        if f.t > max_tex_idx: max_tex_idx = f.t
                        if min(f.v) < min_ind_idx: min_ind_idx = min(f.v)
                        if max(f.v) > max_ind_idx: max_ind_idx = max(f.v)

                    if flags & 0x10000000 == 0x10000000:
                        x3_vertex_ct = data.readInt()
                        for l in xrange(x3_vertex_ct):
                            point_idx = data.readInt()
                            tangent = vec(data.readFloat(), data.readFloat(), data.readFloat())
                            unknown = vec(data.readFloat(), data.readFloat(), data.readFloat())

                if flags & 0x10000000 == 0x10000000:
                    unknown = data.read(40)

        lods.append(lod(lod_size, lod_flags, mats, verts, faces))

        #print 'LOD ', i0, len(verts), len(faces), max_tex_idx, min_ind_idx, max_ind_idx

    return lods


########################################################################################################################


def gen_obj():
    model_files = walk_files('.pbb')
    model_file_count = len(model_files)
    for i, (p, fn) in enumerate(model_files, start=1):
        pfn = '%s/%s' % (p,fn)
        f,e =fn.rsplit('.', 1)
        fno = ('obj/%s.obj' % (f)).lower()

        if os.path.exists(fno):
            print 'Exists %d/%d %s' % (i,model_file_count, fno)
            continue

        print 'Processing %d/%d %s' % (i,model_file_count, fn)
        try:
            #export(pfn, fno)

            with open(pfn) as f:
                lods = get_lods(f.read())
            lods[0].save_obj(fno)

        except Exception, e:
            print 'Error processing %s\n%s' % (pfn, e)
            raise


def gen_thumb(check_exists=True, scenes=None, db=None):
    model_files = walk_files('.pbb')
    model_file_count = len(model_files)
    for i, (p, fn) in enumerate(model_files, start=1):
        pfn = '%s/%s' % (p,fn)

        dbship = None
        if scenes and db:
            scene0 = pfn[11:-4].lower()
            scene = scene0[:-6] if scene0.endswith('_scene') else scene0

            id = scenes.get(scene, '')
            if id:
                dbship = db.ships.find_one({'_id': id})

#            if 'ships' in scene and not dbship:
#                print '{:50} | {:50}'.format(scene0, scene)

        if not dbship or 'size' in dbship:
            continue

        f, e =fn.rsplit('.', 1)
        t = 'ships' if 'ships' in p else 'stations'
        fno = ('thumb/%s/%s.gif' % (t, f)).lower()

        if check_exists and os.path.exists(fno):
            print 'Exists %d/%d %s' % (i,model_file_count, fno)
            continue

        print 'Processing %d/%d %s' % (i,model_file_count, fn)
        try:
            with open(pfn) as f:
                lods = get_lods(f.read(), max_lod=1)
            xt = lods[0].thumb(fno)
            if xt and dbship:
                dbship['size'] = size = dict(w=xt[0], h=xt[1], l=xt[2])
                db.ships.save(dbship)
                print '\tsetting size: {} to {}\n'.format(id, size)

        except Exception, e:
            print 'Error processing %s\n%s' % (pfn, e)


def get_info(scenes):
    model_files = walk_files('.pbb')
    model_file_count = len(model_files)
    ships = []
    for i, (p, fn) in enumerate(model_files, start=1):
        pfn = '%s/%s' % (p,fn)
        f, e =fn.rsplit('.', 1)
        #print 'Processing %d/%d %s' % (i,model_file_count, fn)
        try:
            with open(pfn) as f:
                lods = get_lods(f.read(), max_lod=1, load_mesh=False)

            scene = pfn[11:-4].lower()
            scene = scene[:-6] if scene.endswith('_scene') else scene
            id = scenes.get(scene, '')
            ships.append((65536.0*lods[0].scale/500.0*2, scene, id))
        except Exception, e:
            pass
#            print '\tError processing %s\n%s\n' % (pfn, e)
            
#            raise
    for s, f, id in sorted(ships, reverse=True):
        print '%9.0fm | %-60s | %s' % (s, f, id)
    print len(ships)


def get_ship_scenes(db):
    def get_scene(scene):
        scene1 = scene.replace('\\', '/').lower()
        scene2 = scene1[:-6] if scene1.endswith('_scene') else scene1
#        print '{:50} | {:50}'.format(scene, scene2)
        return scene2
    return {get_scene(s['ship_scene']): s['_id']
            for s in db.ships.find({},{'ship_scene':1}) if isinstance(s['ship_scene'], (str, unicode))}

########################################################################################################################


if __name__=='__main__':
    from pymongo import MongoClient
    db = MongoClient().x3

    scenes = get_ship_scenes(db)
#    get_info(scenes, db)
    gen_thumb(False, scenes=scenes, db=db)
    #gen_obj()
