#$Id$
#s.dobrev 2k4

import base
import svd_util.str as _str

'''_NONE can be imported elsewhere; it is constant singleton; do NOT override/replace;
 use ONLY for func-args default_values and similar, meaning no argument sent;
 and translate to something else - never use as value;
 e.g.  def func1( x=_NONE): return x is _NONE and 'no_arguments' or str(x)

 config.notSetYet IS DIFFERENT THING!
'''
_NONE = _str.notSetYet

class config:
    notSetYet = _str.notSetYet
    '''
    notSetYet lives ONLY here - as singleton; but CAN be overriden/replaced once by app (e.g. with None);
    use only for actual values and NEVER for default_args; use _NONE for default_args
    def func2( x=_NONE):
       if x is _NONE: x = config.notSetYet
       a.v = x

    XXXXXXX   NEVER rely on (_NONE == config.notSetYet) XXXXXXXXX
    XXXXXXX   NEVER rely on bool( config.notSetYet)     XXXXXXXXX
    XXX  if replaced/changed, make sure it is done before any usage of it, like class decls etc.
    '''


def typ_matcher_is( value,typ): return type( value) is typ
typ_matcher_isinstance = isinstance
typ_matcher_issubclass = issubclass

def _type2str( typ):  return getattr( typ, '__name__', str(typ))
def _type2repr( typ): return getattr( typ, '__name__', repr(typ))

class StaticType( object):
    '''StaticType(
        typ,                    #can be None if validator present and does the (needed) checks;
                                # else exact type check is done before validator()
        typ_matcher =None,      #functor( value,base_typ) return bool;
                                # default: type(v) is base_typ
        auto_convert =False,    #if type present and not matching as of value, type(value) is attempted

        validator =None,        #functor( value, instance=optional, name=optional)
                                # a generic set-mediator - replaces typ AND auto_convert -
                                # raise TypeError for wrong type(value), ValueError if wrong range,
                                # and/or autoconvert etc; return value
        default_value =_NONE,   #if anything (not _NONE), lazy (!) set - at first get.
                                # if callable( default_value),
                                #   a generic get-mediator:
                                #   value = default_value( instance=me, name=name)
    )
    '''

    @staticmethod
    def TYPEERROR( typ, value ):
        return 'set type %s with value %r of type %s' % (typ, value, type(value) )

    name = ''   #'<noname-test>'
    def __init__( me,
                typ =None,
                auto_convert =False,
                typ_matcher =typ_matcher_is,
                validator =None,
                default_value =_NONE,
                default_value_wants_instance =False,
        ):
        me.default_value = default_value
        me.default_value_wants_instance = default_value_wants_instance
        me.typ = typ
        me.auto_convert = auto_convert
        me.validator = validator
        me.typ_matcher = typ_matcher
        me._make_validate()

        #test default_value in validator
        # XXX what if validator / typ does not match ?

        if default_value is not _NONE:
            if not callable( default_value):
                default_value = me._validate( default_value )      #could raise something
            #else: no instance/name here; postpone validate at when used in get
        else: default_value = config.notSetYet

        me.default_value = default_value

    def _make_validate( me ):
        raise NotImplemented
        #check typ_matcher, validator, assign me._validator
        me._validate = validator

    def _make_property( me, name):
        me.name = name
        raise NotImplemented
        #return property/descriptor of me

    def test_validator( me, *value_in_out, **k):
        validator = me._validate
        if validator:
            name = me.name or '<noname-test>'
            for v,vout in value_in_out:
                print 'test .validator', me, ': value %s, expect %s;' % (v, vout)
                try:
                    isexc = issubclass( vout, Exception)
                except TypeError: isexc = False

                if not isexc:
                    r = validator( v, name=name, **k)
                    if vout != r:
                        print 'falied For %r: expect %r, got %r' % (v, vout, r)
                    #else: print 'ok'
                else:
                    try:
                        r = validator( v, name=name, **k)
                    except vout:
                        #print 'ok'
                        pass
                    except Exception,r:
                        print 'falied for %r: expect %s, got %s' % (v, vout, r)
                        raise
                    else:
                        print 'falied for %r: expect %s, got %r' % (v, vout, r)

    def __str__( me):
        return (
                (me.name and '%s: ' % me.name or '')
                +(me.__class__.__name__ )
                +'('
                    +_type2str( me.typ)
                    +(me.auto_convert and ', auto_convert' or '')
                    +(me.default_value not in (config.notSetYet, _NONE) and ', default=%s' % _type2repr( me.default_value ) or '')
                    +(me.validator and ', validator=%s' % me.validator or '')
                +')'
            )

    def __call__( me):      #use as ctor
        default_value = me.default_value
        if callable( default_value):
            #if me.default_value_wants_instance:
            #    default_value = default_value( instance=None, name=me.name)
            #else:
                default_value = default_value()
        if default_value is _NONE: default_value = config.notSetYet
        return default_value

       # XXX use for StaticType bases only - Number.makeStaticType() will produce Number()s !!!
    @classmethod
    def makeStaticType( klas, typ):
        if not isinstance( typ, StaticType):# and not issubclass( typ, StaticType):
            try:
                maker = typ.makeStaticType
            except AttributeError:
                typ = klas( typ, default_value=typ)
            else:
                typ = maker( typ)
        return typ

import container

class StaticTyper_factory( base.StaticTyper_factory):
    ''' usage:
        subclass the below StaticTyper, then define in the klas
            name = StaticType(...) for each required attribute.
        note: use the __class__.StaticType[ name] to get the StaticType of name, as
              __class__.name is not the StaticType of name - unless engine3 (descriptors) is used
    '''
    #this metaclassing is required only to pick attribute names.
    # if that is not needed (some internal automatic naming), a simple base class
    # having me._props = StaticType_ValueContainer() in constructor would do

    staticTypes = ( StaticType, )
    Proxy4Container = container.Proxy4Container_order #default looks for ordering!

    @staticmethod
    def convert( me, name, bases, adict, slots_outside_StaticType =()):
        used_types = {}
        types = container.Descriptor4Container( me.Proxy4Container, config.notSetYet )

        for a,t in adict.iteritems():
            if isinstance( t, me.staticTypes):
                idt = id(t)
                #one reference only - type.name is shared!
                if idt in used_types:
                    print 'warning: type %s for %s has been already used in %s' % (t,a, used_types[idt] )
                else:
                    used_types[ idt] = a
                    adict[a] = t._make_property( a)
                    types[a] = t

        StaticType_ValueContainer = me.rebase( types, bases, slots_outside_StaticType )
        adict[ 'StaticType_ValueContainer' ] = StaticType_ValueContainer      #for lazy base._get__props
        adict[ 'StaticType' ] = types
            #use as klas/inst.StaticType[ name]
            # or klas/inst.StaticType.iterkeys/types/values/items;
            # itervalues/items via klas and inst differ
            #see container for description


        #must re-flatten StaticType's and re-make StaticType_ValueContainer / slots
    @classmethod
    def rebase( me, types, bases, slots_outside_StaticType =()):
        slots_outside_StaticType = list( slots_outside_StaticType)
        #flatten hierarchy, keeping already available things in types
        for b in bases:
            try:
                s = b.StaticType
            except AttributeError: pass
            else:
                #only if not already there
                for k,v in s.iteritems():
                    types.setdefault( k,v)
                for k in b.StaticType_ValueContainer.__slots__:
                    if k not in slots_outside_StaticType:
                        slots_outside_StaticType.append( k)

        slots = types.keys() + [ a for a in slots_outside_StaticType if a not in types]
        class StaticType_ValueContainer( object):
            __slots__ = slots       #DONT use any tmp vars in here - only direct extrn reference!
        return StaticType_ValueContainer      #for lazy base._get__props

config._DBG_getsetstate = False

class StaticTyper( base.StaticTyper):
    __metaclass__ = StaticTyper_factory
    __slots__ = ()      #do not introduce __dict__ etc.
    def __str__( me, order =None):
        return _str.make_str( me, me.StaticType.iterkeys( order), name_name='' )
            # name_name is by default 'name', which clashes easily.
            # it can be '_name_', but it is never used anyway:
            #  may only be used eventualy in Struct-class-vars which are instances
            #  of another Struct - but this will need meta-support
    @classmethod
    def _rebase( klas, *bases ):
        klas.__bases__ = tuple( bases)
        klas.__metaclass__.rebase( klas.StaticType, bases, klas.StaticType_ValueContainer.__slots__)

########## pickle-ability
class Mix4pickle( object):
    __slots__ = ()
    def _walkItems( me):
        'only 1 level - non-hierarchical; overload and walk __slots__ if needed'
        return me.StaticType.iteritems()

    def __getstate__( me):
        if config._DBG_getsetstate: print '__getstate__', me.__class__
        state = dict( me._walkItems() )
        return state

    _pickle_translator = {}         #overload
    def __setstate__( me, state):
        if config._DBG_getsetstate: print '__setstate__', me.__class__
        me.__init__()
        klas = me.__class__.__name__
        translator = me._pickle_translator
        for k,v in state.iteritems():
            kk = translator.get(k,k)
            if kk is None: print '__setstate__: ignoring attribute %(klas)s.%(kk)s=%(v)s' % locals()
            else: setattr( me, kk, v)

########## equality
class Mix4eq( object):
    'needs _walkItems - see Mix4eq'
    __slots__ = ()
    _debug_Mix4eq = False
    def __eq__( me, other):
        if me._debug_Mix4eq: print 'eq?', object.__repr__( me), object.__repr__( other)
        if me.__class__ is not other.__class__:
            if me._debug_Mix4eq: print 'diff class'
            return False
        empty=1
        notSetYet = config.notSetYet
        for k,v in me._walkItems():
            empty=0
            ov = getattr( other, k, notSetYet)
            if not (ov == v):
                if me._debug_Mix4eq: print 'diff val', k,`v`,`ov`
                return False
        if empty:
            for k,v in other._walkItems():
                if v is not notSetYet:
                    if me._debug_Mix4eq: print 'one empty, other not', k
                    return False        #not empty -> not same
            #here -> other is empty -> same
        return True

    def __ne__( me, other):
        return not (me == other)




#########

if __name__=='__main__':

    def test( StaticTyper, orderer =None, keys_order =None):
        class boza( StaticTyper):
            def byte_Validator( v, **k_ignore):
                #print 'validate', v
                if v<0 or v>255:
                    raise ValueError, 'value %d must be within 0..255' % v
                return v
            x = StaticType( int)
            y = StaticType( int, validator= byte_Validator, auto_convert =True, default_value =44 )
            y.test_validator(
                (1,1), (0,0), (255,255),    #in range
                ('1',1),                    #in range, auto_convert
                ('0x34', ValueError),       #in range, auto_convert, wrong format #use int(..,0) to autoguess
                (300,    ValueError),       #out range
                ('400',  ValueError),       #out range, auto_convert
                ( list(), TypeError),       #wrong type
              )
            pass

        class boza2( boza):
            z = StaticType( str, auto_convert =True, default_value ='ohh' )
            x = StaticType( str, auto_convert =True, default_value ='xx0' )

        a = boza()

        print '----'
        try: print a.x
        except :
            import traceback
            traceback.print_exc(1)

        print '----'
        a.x = 2 #ok
        print 'x ', a.x

        print '----'
        try: a.x = '2'
        except :
            import traceback
            traceback.print_exc(1)

        print '----'
        print 'y ', a.y

        print '----'
        try: a.y = 500
        except :
            import traceback
            traceback.print_exc(1)

        print '----'
        a.y = '250'
        print 'y ', a.y

        print '===='
        print 'y.type:', a.StaticType[ 'y']
        print 'x.type:', a.StaticType[ 'x']

        b = boza2()
        print '==== boza2'
        print 'z.type:', b.StaticType[ 'z']
        print 'y.type:', b.StaticType[ 'y']
        print 'x.type:', b.StaticType[ 'x']

        def statics( bz, keys_order =None):
            print
            print bz
            keys = list( bz.StaticType.iterkeys() )
            print '.keys',   keys
            if keys_order:
                assert list(keys) == list(keys_order), (keys, keys_order)
            print '.types',  list( bz.StaticType.itertypes() )
            print '.values', list( bz.StaticType.itervalues() )

        print '\n ** UNORDERED:'
        statics( boza2)
        statics( b)
        if orderer:
            orderer( boza2)
        else:
            boza2._order_flat = keys_order = 'z','y','x'
        print '\n ** ORDERED:'
        statics( boza2, keys_order)
        statics( b, keys_order)

    test( StaticTyper)

    if 10:
        ###############
        # example:
        # make .StaticType be a container which uses instance-or-klas._myorder
        class StaticTyper_factory2( StaticTyper_factory):
            class Proxy4Container( container.Proxy4Container_order):
                order_name = '_myorder'
        class StaticTyper2( StaticTyper):
            __metaclass__ = StaticTyper_factory2
            __slots__ = ()      #do not introduce __dict__ etc.

        order = 'x','y','z'
        def orderer( b): b._myorder = order
        test( StaticTyper2, orderer, order)


# vim:ts=4:sw=4:expandtab
