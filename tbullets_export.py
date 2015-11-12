from pyexcel_ods import get_data

def export(data):
    data.sort()
    while not data[0] or data[0][0] == 0.0:
        del data[0]

    for row in data[:3]:
        del row[7]
        del row[6]
        del row[5]
        del row[4]
        del row[3]
        del row[2]
        del row[1]
        del row[0]
    for row in data[3:]:
        if row:
            del row[21]
            del row[19]
            del row[7]
            del row[6]
            del row[5]
            del row[4]
            del row[3]
            del row[2]
            del row[1]
            del row[0]

    def tostr(i, v):
        if 16<=i<=18:
            return str(float(v))
        try:
            return str(int(v)) if float(v) == int(v) else str(float(v))
        except:
            return str(v)

    with open('TBullets.pck', 'w') as of:
        of.write(''.join(r[0]+'\n' for r in data[0:2]))
        of.write(''.join((';'.join(tostr(i, v) for i, v in enumerate(r))+';\n') for r in data[2:] if r))

if __name__ == '__main__':
    data = get_data("tbullets.ods")['tbullets']

    export(data)
