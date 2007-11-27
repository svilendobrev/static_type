#$Id$
"""
base for StaticTyping + structs, autotest, optional, alternative, meta(class-level),
    constant/readonly, UI-metainfo,
"""

import static_type
from static_type.util.attr import issubclass
from static_type.util.str import str_args_kargs, make_str
from static_type.util import class_attr
from static_type import _NONE, config

import warnings
class Messager( object):
    _test = False
    _messages = []
    _errors = []
    class UserError( Warning): pass
    def __init__( me, txt, err =False ):
        me.txt = txt
        me.err = err
    def __call__( me, **kargs):
        pfx = me.err and '!! ERROR: ' or '! warning: '
        t = pfx + (me.txt % kargs)
        me._messages.append( t)
        if me.err: me._errors.append( t)
        if not me._test:
            cat = me.err and me.UserError or UserWarning
            import inspect
            stack = inspect.stack(10)
            level = 0
            try:                #try being too smart...
                for f in stack:
                    filename = f[1]
                    level += 1
                    if 'static_type/' not in filename: break
            finally: del stack
            warnings.warn( t, cat, stacklevel= max(2,level) )
    @classmethod
    def Error( klas, txt): return klas( txt, True)
    @classmethod
    def Warning( klas, txt): return klas( txt, False)

#msg_myArrays_must_be_StaticStruct = Messager.Error( '%(struct)r:\n\t definition of %(member)r not subclass of %(base)s' )
msg_MissingValue = Messager.Warning( '%(struct)r: missing value of %(member)r' )
msg_WrongValue = Messager.Error( '%(struct)r: wrong value of %(member)r = %(value)r\n\t %(e)s' )

#######
config.STRUCT_AUTO_INSTANTIATE = False
config.DISABLE_NON_STATICTYPE_ATTRIBS = True

class StaticTyper_factory( static_type.StaticTyper_factory):
    @staticmethod
    def convert( klas, name, bases, adict):
        slots_outside_StaticType = []
        alts = []
        for p,t in adict.iteritems():
            need_slot = getattr( t, 'need_slot_outside_StaticType', None)
            if callable( need_slot ): need_slot = need_slot()
            if need_slot:
                slots_outside_StaticType.append( p)
            autos = getattr( t, 'auto_StaticTypes', None)
            if autos:
                alts += autos
                for a in autos:
                    f = getattr( a, 'slot_outside_StaticType', None)
                    if f:
                        if callable(f): f = f(p)
                        slots_outside_StaticType.append( f )

        static_type.StaticTyper_factory.convert( klas, name, bases, adict, slots_outside_StaticType= slots_outside_StaticType) or name
        # make x accessible via class.x (not via class.StaticType['x'] - hence after convert())
        for t in alts:
            adict[ t.name ] = t

        # have __slots__ = () automatic in each class   -   do not introduce __dict__ etc.
        adict.setdefault( '__slots__', ())

        for tname,t in adict.iteritems():
            if issubclass( t, static_type.StaticTyper):
                if config.STRUCT_AUTO_INSTANTIATE:
                    adict[ tname ] = class_attr.Descriptor4AutoCreatedReadonlyAttr( t, tname)
                    #or just make it StaticType(t) ?
                else:
                    if config.DISABLE_NON_STATICTYPE_ATTRIBS:
                        adict[ tname ] = class_attr.Descriptor4ClassOnlyAttr( t, tname)

        for p,t in adict[ 'StaticType' ].iteritems():   #flattened
            if t.meta:
                try:
                    v = adict[ p]
                except KeyError:
                    for b in bases:
                        try:
                            bv = getattr( b,p)
                            bt = b.StaticType
                        except AttributeError: continue
                        if p in bt and bt[p] is not bv: #has a value
                            break
                    else:
                        msg_MissingValue( struct=name, member=p )
                    continue
                if v is t: continue     #self - definition
                try:
                    t._validate( v)
                except (TypeError,ValueError), e:
                    msg_WrongValue( struct=name, member=p, value=v, e=e )

############


class StaticType( static_type.StaticType):
    auto_StaticTypes = ()       #used by StaticTyper_factory - optionalism etc
    optional = None
    non_atomary = False
    need_slot_outside_StaticType = False   #if instance of this type is always available - need a slot

    def __set_type_cxx( me,v): me._type_cxx = v
    def __get_type_cxx( me):
        return getattr( me.factory, 'type_cxx', None) or getattr( me.factory, 'name', None) or me._type_cxx or getattr( me.typ, '__name__', None)
    type_cxx = property( __get_type_cxx, __set_type_cxx)

    def __init__( me, type,
                    comment     ='',
                    type_cxx    =None,
                    type_description =None,
                    factory     =None,      #parent factory, e.g. some typedef - to get the name if set later
                    optional    =False,     #False, True (opt but off), 'on' (opt and on)
                    readonly    =False,
                    constant    =False,     #readonly-alias
                    UI_hide =False,         #dontshow in UI
                    UI_width =None,         #field text-width (characters)
                    meta =False,            #True - subclass var - subclasses assign a value
                                            #False- instance var - instances assign a value
                    auto_convert =True,     #if type present and not matching as of value, type(value) is attempted
                    **kargs):

        me.UI_width = UI_width
        me.UI_hide = UI_hide
#        me.type_cxx = type_cxx or getattr( type, '__name__', None)
        me._type_cxx = type_cxx
        me.factory   = factory
        me.type_description = type_description
        me.comment  = comment
        me.readonly = constant or readonly or type is not None and not callable( type)
        me.meta = meta
        static_type.StaticType.__init__( me, typ=type, auto_convert=auto_convert, **kargs)
        if optional:
            me.optional = o = me.OptionalitySwitch( me, optional == 'on' )
            me.auto_StaticTypes = me.auto_StaticTypes + ( o,)

    class OptionalitySwitch( object):
        def __init__( me, parent, default_value =True):
            me.parent = parent
            me.default_value = default_value

        def slot_outside_StaticType( name): return name + '__on'
        slot_outside_StaticType = staticmethod( slot_outside_StaticType)
        def get_name( me): return me.slot_outside_StaticType( me.parent.name)
        name = property( get_name)

        def __get__( me, obj, *args_ignore,**kargs_ignore):
            if not obj: return me
            obj = obj._props
            name = me.name
            try:
                return getattr( obj, name)
            except AttributeError:
                v = me.default_value
                setattr( obj, name, v)
                return v
        def __set__( me, obj, value):
            setattr( obj._props, me.name, value)
        def __str__( me):
            return me.name + ': optionality switch of '+str( me.parent)

    class OptionalOffError( AttributeError): pass

    OPTIONALOFF_GET_IS = None  #None, 'turnon', 'error-whatever'
    OPTIONALOFF_SET_IS_ERROR = True

    def __get__( me, obj, *args,**kargs):
        if obj is None: return me
        optional = me.optional
        if optional is not None and not optional.__get__( obj):
            m = me.OPTIONALOFF_GET_IS
            if m == 'turnon':
                optional.__set__( obj, True)  #turn on
            elif m:         #error - disable get-access
                raise me.OptionalOffError, me.name
        return static_type.StaticType.__get__( me, obj, *args,**kargs)

    def __set__( me, obj, value, initial_default =False):
        if not initial_default:
            if me.readonly:         #this is a kind of validator, actualy...
                raise AttributeError, me.name
            optional = me.optional
            if optional is not None and not optional.__get__( obj):
                if me.OPTIONALOFF_SET_IS_ERROR:     #disable get-access
                    raise me.OptionalOffError, me.name
                else:       #turn on
                    optional.__set__( obj, True)
        return static_type.StaticType.__set__( me, obj, value)

#### auto-testing
    def autotester( me, **kargs): me.tester = me.Test( me, **kargs)

#### description
    def __str__( me):
        return (static_type.StaticType.__str__( me)
                    +(me.optional and ', optional' or '')
                    +(me.readonly and ', readonly' or '')
                    +(me.meta and ', meta' or '')
                 )
    def description( me):
        return me.type_description or '%s:%s' % (me.__class__.__name__, getattr( me.typ, '__name__', str(me.typ)))

#### walking me, members etc
    def walk( me, visitor ):
        walker = getattr( me.typ, 'walk', None)
        if walker:
            try:
                if walker.im_self is None:
                    return    #unbound method, i.e. no info without instance
            except AttributeError: pass
            walker( visitor)

    class Visitor:
        class Frame:
            def __init__( me, typ =None, name ='', obj =_NONE, level =0):
                me.typ = typ
                me.name = name
                if obj is _NONE: obj = config.notSetYet
                me.obj = obj
                me.level = level
            def __str__( me, obj =True):
                return '%s( %s)' % (me.__class__.__name__,
                    str_args_kargs( _filter=lambda k,v: obj or k!='obj', **me.__dict__))
        def __init__( me):
            me.stack = []

        current = property( lambda me: me.stack[-1] )
        def _push( me, *args, **kargs):         #Frameargs
            frame = me.Frame( level=len(me.stack), *args, **kargs)
            me.stack.append( frame)
            return frame
        def _pop( me ):
            return me.stack.pop()

        def do( me, current, walker =None):
            #use current... ==me.current; before
            if walker: walker( me)
            #use current... ==me.current; after

        def use( me, *args, **kargs):           #Frameargs
            c = me._push( *args, **kargs )
            #c = me.current
            me.do( c, getattr( c.typ, 'walk', None) )
            me._pop()

        def fullname( me, delim ='.'):
            names = [ frame.name for frame in me.stack ]
            if names and not names[0]: names = names[1:]
            if delim is None: return names
            return delim.join( names)

        class FrameCollector( list):
            'collect Frame w/fullname'
            def __call__( me, current, visitor):
                current.fullname = visitor.fullname()
                me.append( current )

    class Visitor4getFlat( Visitor):
        @staticmethod
        def printer( current, visitor):
            print visitor.fullname(), current.typ, current.obj

        def __init__( me,
                doer =None,
                meta            =True,      #replace bools with ('off', 'on', 'only') ?
                optional_switch =True,
                optional_off    =True,
                non_atomary     =True,      #container/sequence , struct
                only_if_obj     =False,     #walk inside (non_atomary) only if obj non-empty
                only_if_struct  =False,     #walk inside only if struct
                *args, **kargs):
            me.doer = doer is None and me.printer or doer
            me.meta = meta
            me.optional_switch = optional_switch
            me.optional_off = optional_off
            me.non_atomary = non_atomary
            me.only_if_obj = only_if_obj
            me.only_if_struct = only_if_struct
            StaticType.Visitor.__init__( me, *args, **kargs)

        def _do( me, current): me.doer( current, me)

        _ERROR = False
        def do( me, current, walker =None):
            c = current
            typ = c.typ
            obj = c.obj
            notSetYet = config.notSetYet

            meta = getattr( typ, 'meta', None)
            if meta and not me.meta:
                return
            optional_switch = getattr( typ, 'optional', None)
            if optional_switch:
                parent = me.stack[-2].obj
                if parent is notSetYet: on = notSetYet
                else: on = optional_switch.__get__( parent )
                if me.optional_switch:
                    tmp = me.Frame( name=optional_switch.name, typ=optional_switch, obj=on, level=len(me.stack)-1 )
                    me.stack[-1] = tmp
                    me._do( tmp)
                    me.stack[-1] = c
                if on is not notSetYet and not on:
                    if not me.optional_off:
                        return
            if me.non_atomary or not getattr( typ, 'non_atomary', None):
                me._do( c)

            if not walker: return
            if me.only_if_struct and not issubclass( typ, StaticStruct): return
            if me.only_if_obj and obj is notSetYet: return
            try:
                if walker.im_self is None:
                    return    #unbound method, i.e. no info without instance
            except AttributeError: pass
            try:
                walker( me)
            except:
                if not me._ERROR:
                    me._ERROR = True
                    for f in me.stack: print f
                    print walker
                raise

############

class StaticTyperBase( static_type.StaticTyper):
    __metaclass__ = StaticTyper_factory
    #intermediate level... used in resgen?

from static_type.util.assignment_order import flatten_class__order

class StaticStruct( StaticTyperBase):
    non_atomary = True
    @staticmethod
    def need_slot_outside_StaticType(): return config.STRUCT_AUTO_INSTANTIATE

    @staticmethod
    def _order_maker( klas):
        'use ._order or ._order_flat or else dir()'
        try:
            return flatten_class__order( klas)
        except AttributeError:
            return dir( klas)

    @staticmethod
    def _order_Statics_gettype( klas, k):
        'order filter - raise KeyError if to be excluded'
        return klas.StaticType[ k]

    @classmethod
    def _order_Statics( klas, items =False):
        order = klas._order_maker( klas)
        _order_Statics_gettype = klas._order_Statics_gettype
        for k in order:
            try:
                typ = _order_Statics_gettype( klas, k)
            except KeyError:
                continue
            if items: yield k,typ
            else: yield k

    @classmethod
    def getStaticTypesFlat( klas, pfx ='', obj =_NONE, only_if_obj =None, **kargs):
        'yield Frames'
        collector = StaticType.Visitor.FrameCollector()
        if obj is _NONE: obj = config.notSetYet
        if only_if_obj is None: only_if_obj = obj is not config.notSetYet

        v = StaticType.Visitor4getFlat(
            doer=collector,
            only_if_obj=only_if_obj, **kargs)
        v.use( typ=klas, name=pfx, obj=obj)
        return collector

    @classmethod
    def walk( me, visitor ):
        obj = visitor.current.obj
        for i_name,i_typ in me._order_Statics( items=True):
            o = getattr( obj, i_name, config.notSetYet)
            visitor.use( typ=i_typ, name=i_name, obj=o )

    def __str__( me, **kargs):
        root = StaticType._stack is None
        if root: StaticType._stack = []
        r = make_str( me, me._order_Statics(), name_name='', **kargs)
            # name_name is by default 'name', which clashes easily.
            # it can be '_name_', but it is never used anyway:
            #  may only be used eventualy in Struct-class-vars which are instances
            #  of another Struct - but this will need meta-support
        if root: StaticType._stack = None
        return r
    __repr__ = __str__
    repr = property( __str__)

    def sync_init( me):
        for name,typ in me.StaticType.itertypes():
            try: f = typ.sync_init
            except AttributeError: pass
            else: f()

    def __init__( me, **kargs_ignore):
        me.sync_init()

        if 0:
            #this has to be done AFTER all containers already exist (without slaves)
            #tradeoff - all these members will always appear (creating is non lazy)
            #now - done lazily when setattr( obj._props)
            for name,typ in me.StaticType.itertypes():
                try: f = typ.sync_setup
                except AttributeError: pass
                else: f( me)

    @classmethod
    def makeStaticType( klas, *args_ignore, **kargs):
        return klas.SubStruct( klas, **kargs)
    Instance = makeStaticType


class SubStruct( StaticType):
    non_atomary = True
    forward = False         #see forward.py : A.a->A and A.b->B.a->A
    auto_set = True         #default; can be overriden per klas in StaticStruct, or per Instance()
    def __init__( me, type, auto_set =None, default_value =_NONE, factory =None, **kargs):
        assert issubclass( type, StaticStruct)
        if auto_set is None: auto_set = getattr( type, 'auto_set', me.auto_set)
        if auto_set: default_value = type
        StaticType.__init__( me, type=type, default_value=default_value, factory=factory or type,
            typ_matcher= static_type.typ_matcher_isinstance,
            **kargs)

    def getStaticTypesFlat( me, *args, **kargs):
        return me.typ.getStaticTypesFlat( *args, **kargs)
    def _order_Statics( me, *args, **kargs):
        return me.typ._order_Statics( *args, **kargs)
StructInstance = SubStruct
StaticStruct.SubStruct = SubStruct
############

class Syncer( object):
    _sync_masters = ()
    def sync_add_master( me, s, do_other =False):
        if s is not me:
            assert isinstance( s, Syncer)
            _sync_masters = me._sync_masters
            if _sync_masters == ():
                _sync_masters = me._sync_masters = []
            if s not in _sync_masters: _sync_masters.append( s)
            if do_other: s.sync_add_slave( me, do_other=False)

    _sync_slaves = ()
    def sync_add_slave( me, s, do_other =False):
        if s is not me:
            assert isinstance( s, Syncer)
            _sync_slaves = me._sync_slaves
            if _sync_slaves == ():
                _sync_slaves = me._sync_slaves = []
            if s not in _sync_slaves: _sync_slaves.append( s)
            if do_other: s.sync_add_master( me, do_other=False)

    def __init__( me,
                    sync_masters =None,    # list-of-other Syncers
                    sync_slaves  =None,    # list-of-other Syncers
                ):
        if sync_slaves is not None:
            if isinstance( sync_slaves, Syncer.DualList):
                sync_slaves.append( me)
            me._sync_slaves = sync_slaves
        if sync_masters is not None:
            if isinstance( sync_masters, Syncer.DualList):
                sync_masters.append( me)
            me._sync_masters = sync_masters

    def _sync_init( me, lst, slaves =True ):
        dual = isinstance( lst, me.DualList)
        for s in lst:
            if dual or not slaves: s.sync_add_slave( me)
            if dual or slaves: s.sync_add_master( me)

    def sync_init( me ):
        me._sync_init( me._sync_masters, slaves=False)
        me._sync_init( me._sync_slaves,  slaves=True)

    class DualList( list): #pass
        def zinit( me, slave =True):
            for s in me:
                _sync_masters = s._sync_masters
                _sync_slaves = s._sync_slaves
                for m in me:
                    if m not in _sync_masters: _sync_masters.append( m)
                    if m not in _sync_slaves: _sync_slaves.append( m)

############

def str_min_max( me, pfx=', size'):
    min = me.min
    max = me.max
    if min or max is not None:
        if min is None: min = ''
        if max is None: max = ''
        return pfx+' %s..%s' % (min, max)
    return ''

class Sizer( object):
    'size limits = min, max, default'
    def __init__( me,
                    min_size    = 0,        #min size allowed
                    max_size    = None,     #max size allowed, None: unlimited
                    constant_size = False,
                    default_size = None,
                    min         = _NONE,    #alias for min_size
                    max         = _NONE,    #alias for max_size
                    **kargs):

        if min in (_NONE, None): min = min_size
        if max is _NONE: max = max_size
        if constant_size:
            if default_size:
                min = default_size
            max = min

        if min in (_NONE, None): min = min_size     #XXX repeat?? why?
        if min<0: min=0
        assert max is None or min <= max
        me.min = min
        me.max = max
        if not constant_size:
            if default_size:
                assert min<= default_size and max is None or default_size <= max
        me.default_size = default_size
        return kargs

    constant_size = property( lambda me: me.min==me.max )

    def __str__( me):
        min = me.min
        max = me.max
        if not min and max is None: return ''
        if min == max:
            r = ', size %(min)s const'
        else:
            if min is None: min = ''
            if max is None: max = ''
            r = ', size %(min)s..%(max)s'
            default_size = me.default_size
            if default_size: r+= '/default %(default_size)s'
        return r % locals()

    def validate( me, value):
        l = len( value)
        min = me.min
        max = me.max
        if l < min:
            raise ValueError, 'value %r size(%d) shorter than min size %r' % (value,l,min)
        if max is not None and l > max:
            raise ValueError, 'value %r size(%d) longer than max size %r' % (value,l,max)
        return value

############ typ_matcher's

def typ_matcher_lessthan( value,typ): return type( value) <= typ

############ validator's

def validator_empty( value, **kargs_ignore): return value

###########################
###########################

# vim:ts=4:sw=4:expandtab
