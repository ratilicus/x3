#!/usr/bin/python

''' cat/dat extractor
    based on:
        post by: akruppa
        on:  Fri, 17. Jan 14, 23:37    Post subject: [LINUX] Python script for cat/dat file extraction
        at: http://forum.egosoft.com/viewtopic.php?t=361709
    modified from above to extract multiple files and decompress some file types

'''
import os
import sys
import os.path
import zlib

try:
    import config
except:
    print 'config.py not found, please run setup.sh before using this script!'
    exit(1)

class cat(object):
    def __init__(self, catfilename, outpath, db=None):
        self.catfilename = catfilename
        self.outpath = outpath
        self.db = db
        with open(catfilename, "rb") as inputfile:
            data = inputfile.read()
        lines = self.cat_decrypt(data).splitlines()
        self.datfilename = lines.pop(0)
        self.entries = {}
        nextpos = 0
        for line in lines:
            name, length = line.rsplit(" ", 1)
            length = int(length)
            self.entries[name] = (nextpos, length)
#            print('%-100s%20s (%s)' % (name, nextpos, length))
            nextpos += length
        try:
            self.datfile = open(os.path.dirname(catfilename) + '/' + self.datfilename, "rb")
#        except FileNotFoundError:
        except IOError as e:
            self.datfile = open(os.path.dirname(catfilename) + '/' +
                    os.path.basename(catfilename).split(".")[0] + ".dat", "rb")

    @staticmethod
    def cat_magic():
        magic = 0xDA
        while True:
            magic = (magic + 1) % 256
            yield magic

    @staticmethod
    def cat_decrypt(data):
        magic = cat.cat_magic()
        return ''.join(chr(ord(b) ^ next(magic)) for b in data)

    def list(self):
        for e, v in sorted(self.entries.items()):
            print('%-100s%s (%s)' % (e, self.catfilename, v[1]))
        return []
        #return sorted(tuple(e for e in self.entries.keys() if e.startswith('objects/ships/')))

    def read_dat(self, pos, length):
        self.datfile.seek(pos)
        return ''.join(chr(ord(b) ^ 0x33) for b in self.datfile.read(length))

    def read_file(self, filename):
        if not filename in self.entries:
            return None
        return self.read_dat(*self.entries[filename])

    def copyall(self):
        for e, v in sorted(self.entries.items()):
            self.copyfile(e)

    def copyfile(self, filename):
        data = self.read_file(filename)
        if not data:
            sys.stderr.write("Could not file %s\n" % filename)
            return

        if filename.endswith(('.pck', '.pbd', '.pbb')):
            rdata=None
            for v in range(255):
                try:
                    data = zlib.decompress(data, v)
                    break
                except:
                    continue

        outfile = '{}/{}'.format(self.outpath, filename.lower())
        if self.db:
            self.db.files.insert({
                'cat': self.catfilename,
                'filename': filename,
                'outfile': outfile
            })
        print '{:30} > {}'.format(self.catfilename, outfile)
        try:        
            os.makedirs(os.path.dirname(outfile))
        except:
            pass
        with open(outfile, "wb") as outputfile:
            outputfile.write(data)

if __name__=='__main__':
    import pymongo
    mongo=pymongo.MongoClient()
    db=mongo.x3

    args = sys.argv[1:]
    if not args:
        print("%s <cat file name | --all>" % sys.argv[0])
    elif args[0] == '--all':
        db.files.drop()
        catpath = config.TC
        tccats = sorted(f for f in os.listdir(catpath) if f.endswith('.cat'))
        for f in tccats:
            c = cat(
                catfilename='{}/{}'.format(catpath, f),
                outpath='{}/tc'.format(config.PWD),
                db=db
            )
            c.copyall()

        catpath = '{}/addon'.format(config.TC)
        apcats = sorted(f for f in os.listdir(catpath) if f.endswith('.cat'))   
        for f in apcats:
            c = cat(
                catfilename='{}/{}'.format(catpath, f),
                outpath='{}/ap'.format(config.PWD),
                db=db
            )
            c.copyall()
    else:
        c = cat(
            args[0],
            outpath=('{}/ap' if 'addon' in args[0] else '{}/tc').format(config.PWD)
        )
        c.copyall()
