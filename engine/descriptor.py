#$Id$
#s.dobrev 2k4

from main import StaticType, StaticTyper, _NONE, config

#a descriptor instead of property
#probably slower than statictype2 but more flexible

# XXX maybe:
# class Klas:
#  StaticType = StaticType_container_and_factory()
#  a= StaticType( ...)  - auto register, in correct order etc
# may remove need of _order and partialy metaclass'ing (names cannot be obtained other way)

def _setattr_props( obj, name, value):
    if value is config.notSetYet:
        delattr( obj, name)
    else:
        setattr( obj, name, value)

class StaticTyper( StaticTyper):
    _debug_props_get_set = 0
    __slots__ = ()
    def _setattr_props( me, name, value, type =None):
        _setattr_props( me._props, name, value)

class StaticType( StaticType):
    _stack = None   #XXX to catch recursive get-operations set this as []

    def _setattr_props( me, obj, name, value):      #obj is the parent struct
#        print '_setattr_props', name, value
        if isinstance( obj, StaticTyper):
            obj._setattr_props( name, value, me)
        else:
            _setattr_props( obj, name, value)

    def _make_property( me, name):
        me.name = name
        return me

    def _no_default_value( me):
        value = me.default_value
        return value is config.notSetYet or value is _NONE

    def _set_default_value( me, obj):
        if me._no_default_value(): raise
        value = me.default_value
        if callable( value):    #sort-of generator - e.g. timestamp, checksum etc
            _stack = me._stack
            name = me.name
            #print 'setdef', name, id(me), id(obj), _stack
            if _stack is not None:
                if id(me) in _stack:
                    klas = obj.__class__
                    print '!!! recursive set_default_value: %(klas)s.%(name)s = %(value)s(); check auto_set/default_value' % locals()
                    raise  #break recursion
                _stack.append( id(me) )
            if me.default_value_wants_instance:
                value = value( instance=obj, name=name)
            else:
                value = value()
        value = me.__set__( obj, value, initial_default=True)
        return value

    def __get__( me, obj, klas =None, no_defaults =False):
        if obj is None: return me
        name = me.name
        #if obj._debug_props_get_set: print 'getattr', name

        try: value = getattr( obj._props, name)
        except AttributeError:
            if no_defaults: raise
            value = me._set_default_value( obj)
            #_stack.pop()   DONT!
            #XXX DO NOT touch stack-stuff, esp. do not remove items from it!
            #XXX if this catches recursion, either there IS recursion or needs completely different solution
            #XXX see types/forward.py testing for a recursive auto_set B-C-B-C...
            #XXX e.g. r2661 breaks it:
            #   if _stack and id(me) in _stack: _stack.remove( id(me) )
        return value

    def __set__( me, obj, value, initial_default =False):
        ''' must return value '''
        name = me.name
        assert name
        #if obj._debug_props_get_set: print 'setattr', name,value
        if value is not config.notSetYet:
            #print type(value),id(value),id(config.notSetYet),value
            value = me._validate( value, obj)       #could raise something
        me._setattr_props( obj, name, value)
        return value

    def __delete__( me, obj):   # XXX
        '''not really delete, but _unset_.
        go via _setattr_props( notSetYet), to avoid paralel overloading
         - if not allowed - what to do if not?
         - if has default_value, use that one instead, as in __get__?
                or wait and let __get__ do it whenever used explicitly?
        '''
        #if obj._debug_props_get_set: print 'delattr', me.name
        me._setattr_props( obj, me.name, config.notSetYet)

    ######## replacing statictype2's constructed validator
    def _check_type_validator( me ):
        " overload with empty if ALL typecheck is in overloaded _validate"
        if not me.typ:
            assert callable( me.validator)
        else:
            assert callable( me.typ_matcher)

    def _make_validate( me ):
        me._check_type_validator()

    def _validate( me, value, obj =None, **kargs_ignore):
        value = me.validate_typecheck( value)
        value = me.validate_validator( value, obj)
        return value

    ######## separate validators
    def validate_typecheck( me, value, **kargs_ignore):
        typ = me.typ
        if typ and not me.typ_matcher( value,typ):
            auto_convert = me.auto_convert
            if auto_convert:
                try:
                    if callable( auto_convert):
                        value = auto_convert( value, typ)      #could raise something
                    else:
                        value = typ( value)      #could raise something
                except (TypeError, SyntaxError), e:
                    e.args = ( me.TYPEERROR( typ, value) +' :\n auto_convert: '+ e.args[0] ,)
                    raise
            else:
                raise TypeError, me.TYPEERROR( typ, value)
        return value

    def validate_validator( me, value, obj =None, **kargs_ignore):
        validator = me.validator
        if not callable( validator): return value
        name = me.name
        try:
            return validator( value, instance=obj, name=name)
        except (TypeError,ValueError), e:
            print `name`, `e.args[0]`
            e.args = ( 'set attribute "'+name+'": ' + e.args[0], )
            raise


#########

if __name__=='__main__':

    class AA( StaticTyper):
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

    class BB( AA):
        z = StaticType( str, auto_convert =True, default_value ='ohh' )
        x = StaticType( str, auto_convert =True, default_value ='xx0' )

    a = AA()

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

    b = BB()
    print '==== BB'
    print 'z.type:', b.StaticType[ 'z']
    print 'y.type:', b.StaticType[ 'y']
    print 'x.type:', b.StaticType[ 'x']

    print '===='
    print 'a.items',  list( a.StaticType.iteritems() )
    print 'b.items',  list( b.StaticType.iteritems() )
    print 'a.types',  list( a.StaticType.itertypes() )
    print 'b.types',  list( b.StaticType.itertypes() )

# vim:ts=4:sw=4:expandtab
