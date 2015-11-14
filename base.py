from collections import OrderedDict

class Field(object):
    data_field = True
    field_count = 0
    name = None
    label = None
    def __new__(cls, *args, **kwargs):
        self = super(Field, cls).__new__(cls, *args, **kwargs)
        self.field_order = Field.field_count
        Field.field_count +=1
        return self

    def __init__(self, label, *args, **kwargs):
        self.label = label

    def bind(self, model, fieldname):
        ''' bind field to model '''
        self.model = model
        self.name = fieldname
        return self.field_order

    def serialize(self, model, data):
        ''' import pck data '''
        value = data.pop(0)
        return int(value)
    
    def pprint(self, data, indent=0):
        ''' pretty print '''
        print '{}{} = {}'.format(' '*indent, self.label, repr(data[self.name]))

    def __repr__(self):
        return '<{}>(<{}>, "{}", "{}")'.format(self.__class__.__name__, self.model.__name__, self.name, self.label)

    def dump(self, data):
        ''' export json data '''
        return data[self.name]

    def load(self, model, data):
        ''' import json data '''
        return data[self.name]

    
class IntField(Field):
    def serialize(self, model, data):
        ''' import pck data '''
        value = data.pop(0)
        return int(value)


class FloatField(Field):
    def serialize(self, model, data):
        ''' import pck data '''
        value = data.pop(0)
        return float(value)


class StringField(Field):
    def serialize(self, model, data):
        ''' import pck data '''
        value = data.pop(0)
        return str(value)


class ListField(Field):
    def __init__(self, sub_model, label, count=None, count_field=None):
        self.sub_model = sub_model
        self.count = count
        self.count_field = count_field
        self.label = label

    def serialize(self, model, data):
        ''' import pck data '''
        if self.count:
            loops = self.count
        else:
            loops = model.data[self.count_field]

        data_list = []
        for i in xrange(loops):
            data_list.append(self.sub_model.serialize(data))
        return data_list

    def pprint(self, data, indent=0):
        ''' pretty print '''
        print '{}{}:'.format(' '*indent, self.label)
        for sub_model in data[self.name]:
            sub_model.pprint(indent+2)

    def dump(self, data):
        ''' export json data '''
        out = []
        for sub_model in data[self.name]:
            out.append(sub_model.dump())
        return out


    def load(self, model, data):
        ''' import json data '''
        out = []
        for item_data in data[self.name]:
            out.append(self.sub_model.load(item_data))
        return out


class CalcField(Field):
    data_field = False

    def __init__(self, label, fn):
        self.fn = fn
        self.label = label

    def serialize(self, model, data):
        ''' import pck data '''
        raise Exception('Cannot serialize a non-data field')

    def load(self, model, data):
        ''' import json data '''
        raise Exception('Cannot serialize a non-data field')

    def dump(self, model, data):
        ''' import json data '''
        raise Exception('Cannot dump a non-data field')

    def value(self, model):
        return self.fn(model)

def calc_field(label):
    def inner(fn):
        return CalcField(label, fn)
    return inner

class ModelMetaClass(type):

    def __new__(cls, name, parents, attrs):
        attrs.pop('__module__')
        abstract = attrs.pop('__abstract__', False)
        if not abstract:
#            print 'MMC', cls, name,parents, attrs.keys()
            fields = []
            for fieldname, fieldinst in tuple(attrs.items()):
                if issubclass(fieldinst.__class__, Field):
                    fields.append((fieldname, fieldinst))
                    del attrs[fieldname]
        cls_type = super(ModelMetaClass, cls).__new__(cls, name, parents, attrs)
        if not abstract:
            fields.sort(key=lambda f: f[1].bind(cls_type, f[0]))
            cls_type._fields = OrderedDict(fields)
        return cls_type
        
class Model(object):
    __abstract__ = True
    __metaclass__ = ModelMetaClass
    data = None

    def __init__(self):
        self.data = OrderedDict()

    def pprint(self, indent=0):
        ''' pretty print '''
        print '{}{}:'.format(' '*indent, self.__class__.__name__)

        for fieldname, fieldinst in self._fields.items():
            fieldinst.pprint(self.data, indent+2)

    def __getattr__(self, attr):
        if attr in self._fields:
            if attr in self.data:
                return self.data[attr]
            else:
                return self._fields[attr].value(self)
        return super(Model, self).__getattr__(attr)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def dump(self):
        ''' export json data '''
        data = OrderedDict()
        for fieldname, fieldinst in self._fields.items():
            if fieldinst.data_field:
                data[fieldname] = fieldinst.dump(self.data)
        return data

    @classmethod
    def serialize(cls, data):
        ''' import pck data '''
        self = cls()
        for fieldname, fieldinst in self._fields.items():
            if fieldinst.data_field:
                self.data[fieldname] = fieldinst.serialize(self, data)
        return self

    @classmethod
    def load(cls, data):
        ''' import json data '''
        self = cls()
        for fieldname, fieldinst in self._fields.items():
            if fieldinst.data_field:
                self.data[fieldname] = fieldinst.load(self, data)
        return self
