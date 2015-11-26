import re
import struct
import os

line_pat = re.compile(r'([ ]*\{[ ]*0x\d+;[ ]*)(-?\d+);[ ]*(-?\d+);[ ]*(-?\d+)(;.*)')

name_pat = re.compile(r'[ ]*P[ ]*(\d+);[ ]*B[ ]*([^ ;]+).*')


files=(
    ('tc', 'ships/M6/Boron_M6X', 'ships/M6/Boron_M6X_Scene', 0.5),
#    ('tc', 'ships/M7/Boron_M7',     'ships/m7/boron_m7_scene', 3.0),
#    ('tc', 'ships/M7/Split_M7s',    'ships/m7/split_m7s_scene', 2.0),
#    ('tc', 'ships/M7/Split_M7',     'ships/m7/split_m7_scene', 2.0),
#    ('tc', 'ships/M7/Argon_M7',     'ships/m7/argon_m7_scene', 2.0),
#    ('tc', 'ships/M7/Paranid_M7',   'ships/M7/Paranid_M7_scene', 2.0),
#    ('tc', 'ships/M7/Teladi_M7',    'ships/m7/teladi_m7_scene', 2.0),
#    ('tc', 'ships/Pirate/Pirate_M7','ships/Pirate/Pirate_M7_scene', 2.0),
)

dock_tpl = '''
P %d; B 19103; C 1; N B19103_01; b
{ 0x2002;  0; -100000; 0;  0.000000; 0.000000; 0.000000; 0.000000;  -1; 1; }
'''

def mkdirs(fn):
    try:
        os.makedirs(os.path.dirname(fn))
    except:
        pass

def parse_pbb(src, fn, mf, div, commit=True):
    in_fn = '{}/objects/{}'.format(src, fn)
    out_fn = 'mods/objects/{}'.format(mf)
    data = open(in_fn, 'rb').read()
    pos = data.index('POIN', 0)-8
    
    raw = data[pos:pos+4]
    raw_hex = '{:02x} {:02x} {:02x} {:02x}'.format(*struct.unpack('BBBB', raw))
    size = struct.unpack('>l', raw)[0]
    scale = int(size/65536.0)
    scalem = 65536.0*scale/500.0*2
    text = '{:10} | {} | {:10.2f}'.format(size, raw_hex, scalem)

    size2 = size / div
    scale2 = size2 /65536.0
    scalem2 = 65536.0*scale2/500.0*2
    raw2 = struct.pack('>l', size2)
    raw2_hex = '{:02x} {:02x} {:02x} {:02x}'.format(*struct.unpack('BBBB', raw2))
    text2 = '{:10} | {} | {:10.2f}'.format(size2, raw2_hex, scalem2)
    out_data = data[0:pos] + raw2 + data[pos+4:]
    if commit:
        mkdirs(out_fn)
        with open(out_fn, 'wb') as of:
            of.write(out_data)

    print '{:60} | {} -> {}'.format(fn, text, text2)

def parse_scene_pbd(src, fn, osf, div, commit=True):
    in_fn = '{}/objects/{}'.format(src, fn)
    out_fn = 'mods/objects/{}.pbb'.format(osf)
    in_lines = open(in_fn, 'r').read().split('\n')
    out_lines = []
    names = []
    p = 0
    for line in in_lines:
        res = line_pat.findall(line)
        if res:
            s, x, y, z, e = res[0]
            out = '{}{}; {}; {}{}'.format(s, int(int(x)/div), int(int(y)/div), int(int(z)/div), e)
        else:
            res = name_pat.findall(line)
            if res:
                p = int(res[0][0]) 
                if res[0][1].startswith('ships\\') and not res[0][1].startswith('ships\\props\\'):
                    names.append(res[0][1])
            out = line
        out_lines.append(out)
        
    out_lines.append(dock_tpl%(p+1))
    if len(names) != 1:
        raise Exception('Expected a single pbb name for ship {}, got {}'.format(fn, names))

    if commit:
        mkdirs(out_fn)
        with open(out_fn, 'w') as of:
            of.write('\n'.join(out_lines))
    return names[0].replace('\\','/')

commit = True

if __name__=='__main__':
    for src, fn, osf, div in files:
        mf = parse_scene_pbd(src, fn+'_scene.pbd', osf, div, commit)
        parse_pbb(src, fn+'.pbb', mf+'.pbb', div, commit)

