#$Id$

from static_type.types.base import _NONE, config, StaticType, Syncer, Sizer, str_min_max, Messager
#above static_type.types. because of test.test_base
from static_type.engine.main import typ_matcher_is

################

_numeric_types = [ bool, int, long, float ]
def typ_matcher_numeric_lessthan( value,typ):
    t = type( value)
    try:
        i = _numeric_types.index(t)
    except ValueError: return False
    return i <=_numeric_types.index( typ)
    #return t in _numeric_types and t <= typ

class Number( StaticType, Syncer):
    """
        autoconvert as-is works only over numeric values, i.e. 0x54 won't work.
        int( '0x54') -> TypeError
        needs int( '0x54', 0)
    """
    def __init__( me,
            typ =int,       #actual type of elements
            min =None,      #min value
            max =None,      #max value
            typ_matcher =typ_matcher_numeric_lessthan,
            **kargs
        ):

        try:                        #allow type=.. instead of typ=..
            typ = kargs[ 'type']
            del kargs[ 'type']
        except KeyError: pass

        if type(max) is long  and typ<long : typ = long
        if type(max) is float and typ<float: typ = float

        if min is not None and max is not None:
            assert min <= max
        me.min = min
        me.max = max
        StaticType.__init__( me, typ,
                typ_matcher= typ_matcher,
                **kargs
        )

    def _validate( me, value, obj =None, **kargs_ignore):
        if isinstance( value, str): value = value.replace( ' ','')  #allow separating spaces
        value = me.validate_typecheck( value)
        value = me.validate_minmax( value, obj)     #before or after .validator?
        value = me.validate_validator( value, obj)
        return value

    def validate_minmax( me, value, obj =None, **kargs_ignore):
        min = me.min
        max = me.max
        if min is not None and min > value or max is not None and max < value:
            raise ValueError, '%r outside range [%r:%r]' % (value, min, max)
        return value

    def __str__( me):
        return StaticType.__str__(me) + str_min_max( me, ', range')
    def description( me):
        r = me.__class__.__name__
        r+= ' '+ (me.type_description or me.typ.__name__)
        return r + str_min_max( me, ',')

    ##### sync/bind with Sequence size or something else - no setup as nowhere to store the funcs
    def sync_get_slave_func( me, obj):
        return lambda value: me.__set__( obj, value)
    def _setattr_props( me, obj, name, value ):
        StaticType._setattr_props( me, obj, name, value )
        #XXX what if value is notSetYet, i.e. unset?
        for typ in me._sync_slaves:
            typ.sync_get_slave_func( obj)( value)

################

class Bool( Number):    #separate - allow having separate class-attributes than base Number
    """ warning: bool('False') == True !
        i.e. autoconvert as-is won't work over non-numeric value.
    """
    @staticmethod
    def _autoconvert( value, typ):
        if isinstance( value, str):
            try:
                return typ(int(value))
            except ValueError:
                return value=='True'
        return typ( value )

    def __init__( me, auto_convert= True,
                typ_matcher =typ_matcher_is,
                type_cxx= 'bool',
                **kargs):
        if auto_convert and not callable( auto_convert):
            auto_convert = me._autoconvert
        return Number.__init__( me, min=0, max=1, type=bool,
                auto_convert= auto_convert,
                typ_matcher= typ_matcher,
                type_cxx= type_cxx,
                **kargs)
    def description( me): return me.type_description or ''      #empty by default

################
msg_Empty = Messager.Warning( '%(struct)s: empty %(what)s' )
msg_OutOfRange = Messager.Error( '%(struct)s: %(what)s out of range: %(member)r (%(value)r)' )
msg_DuplicateValue = Messager.Error( '%(struct)s: %(what)s duplicated: %(member)r (%(value)r)' )

class AKeyFromDict( StaticType):
    class AKeyFromDict_reverse( object):
        def get_name( me): return me.parent.name + '_alt'
        name = property( get_name)
        def __init__( me, parent, dict, use_key_and_value =''):
            me.parent = parent
            me.use_key_and_value = use_key_and_value
            me.reverse = reverse = dict.__class__()
            for key,value in dict.iteritems():
                if use_key_and_value:
                    value = me.use_key_and_value % locals()
                if value not in reverse:
                    reverse[ value] = key
                else:
                    msg_DuplicateValue( struct=me, what='dict value', member=key, value=value )
        def __get__( me, obj, *args,**kargs):
            if obj is None: #class.attribute
                return me
            parent = me.parent
            value = parent.__get__( obj, *args,**kargs)
            if obj:
                key = value
                value = parent.dict[ key]
                if me.use_key_and_value:
                    value = me.use_key_and_value % locals()
            return value
        def __set__( me, obj, value):
            try:
                value = me.reverse[ value]
            except KeyError:
               raise ValueError, 'value %r not in allowed values' % (value,)
            return me.parent.__set__( obj, value)
        def __str__( me):
            return (me.parent.__str__() + ', reverse as ' + me.name)
        def lister( me, **kargs_ignore):
            return me.reverse.keys()

        def __getattr__( me, name): return getattr( me.parent, name)

    REVERSE_KEY_AND_VALUE ='%(key)s: %(value)s'

    def __init__( me, dict, dictname ='', validator =None, type =None,
                    auto_default_value =False,              #if no default_value, use first key as default_value
                    use_reverse =REVERSE_KEY_AND_VALUE,     #bool or format(key,value)
                **kargs ):
        me.dict = dict
        me.dictname = dictname
        if not dict:
            msg_Empty( me, what='dict' )
        if validator:
            for k in dict:
                if not validator( k):
                    msg_OutOfRange( struct=me, what='dict key', member=k, value= dict[k] )
        StaticType.__init__( me, type, validator=validator, **kargs )
        if me.default_value in (config.notSetYet, _NONE) and auto_default_value:       #get first one
            for k in dict:
                me.default_value = k
                break
        if use_reverse:
            me.StaticType_alt = me.AKeyFromDict_reverse( me, dict,
                                    use_key_and_value= isinstance( use_reverse, str) and use_reverse or None )
            me.auto_StaticTypes = me.auto_StaticTypes + ( me.StaticType_alt, )

    def _check_type_validator( me ): pass
    def _validate( me, value, obj =None, **kargs_ignore):
        value = me.validate_typecheck( value)
        if value not in me.dict:
            raise ValueError, 'value %r not in allowed values' % (value,)
        value = me.validate_validator( value, obj)
        return value

    def __str__( me):
        return StaticType.__str__( me) + ' ' + me.dictname
    def description( me): return me.type_description or ''      #empty by default

    def lister( me, **kargs_ignore):
        return me.dict.keys()

################

class Text( StaticType, Sizer):
    def __init__( me, type_description ='',
                    UI_width = None,
                    **kargs):
        kargs = Sizer.__init__( me, **kargs)
        UI_width = UI_width or me.max
        StaticType.__init__( me, str,
            type_description=type_description or me.__class__.__name__,
            UI_width=UI_width,
            **kargs)

    def _validate( me, value, obj =None, **kargs_ignore):
        value = me.validate_typecheck( value)
        value = me.validate_validator( value, obj)
        Sizer.validate( me, value)
        return value
    def __str__( me):
        return StaticType.__str__( me) + Sizer.__str__( me)
    def description( me):
        return StaticType.description(me) + Sizer.__str__( me)
    def size( me): raise NotImplemented

################

if __name__ == '__main__':

    from static_type.test.test_base import Test

    class Test4Number( Test):
        def get_testValue_ok( me, **kargs_ignore):
            v = me._testValue_ok
            if v is me._NONEl:
                min = me.victim.min
                max = me.victim.max
                if min is not None: v = [ min ]
                elif max is not None: v = [ max ]
                else: v = [ me.typ() ]
            #print '---ok', me, v
            return v
        def get_testValue_err( me, **kargs_ignore):
            v = me._testValue_err
            if v is me._NONEl:
                min = me.victim.min
                max = me.victim.max
                if min is not None: v = [ min-1 ]
                elif max is not None: v = [ max+1 ]
            #print '---err', me, v
            return v
    Number.Test = Test4Number

    class Test4Bool( Test):
        def get_testValue_err( me, **kargs_ignore):
            v = me._testValue_err
            if v is me._NONEl:
                if me.victim.auto_convert:
                    v = ()   #all is boola'able
                else:
                    v = [ 2, -1, 'false', 'no', None ]
            return v
    Bool.Test = Test4Bool

    class Test4AKeyFromDict( Test):
        def get_testValue_ok( me):
            v = me._testValue_ok
            victim = me.victim
            me_dict = victim.dict
            if not me_dict:
                msg_Empty( victim, what='dict' )
                v = me._NONEl
            else:
                if v is me._NONEl:
                    if 1:
                        v = me_dict.keys()
                    else:
                        for v1 in me_dict.iterkeys():
                            break
                        v = [ v1 ]
                for v1 in v:
                    assert v1 in me_dict
            return v
        def get_testValue_err( me):
            v = me._testValue_err
            victim = me.victim
            me_dict = victim.dict
            if not me_dict:
                msg_Empty( victim, what='dict' )
                v = me._NONEl
            else:
                if v is me._NONEl:
                    v = [ 'anykey %s' % id(victim) ]
                for v1 in v:
                    assert v1 not in me_dict
            return v
    AKeyFromDict.Test = Test4AKeyFromDict

################


if __name__ == '__main__':
    import unittest
    from base import StaticStruct
    from static_type.test.test_base import test, _test_Base, _test_str_empty_mnp
    class t_Base( _test_Base, unittest.TestCase): pass

    class t_Number( t_Base):
        def test_0_set_value( me):
            class A( StaticStruct):
                m = Number( auto_convert=False,)
                m.autotester(
                            testValue_ok = {
                                4       :4,
                                True    :True,  #True==1, bool<=int
                                False   :False, #False==0
                            },
                            testValue_err = [
                                4.0,            #float>int
                                '4', 'r', None,
                                'True',
                            ]
                    )
                n = Number( auto_convert=True,)
                n.autotester(
                            testValue_ok = {
                                4       :4,
                                True    :True,  #True==1, bool<=int
                                False   :False, #False==0
                                '4'     :4,
                            },
                            testValue_err = [
                                'r', None,
                                'True',
                            ]
                    )
                p = Number( min =5, max =9,)
                p.autotester(
                            testValue_ok = {
                                5   :5,
                                9   :9,
                                9   :9,
                                6.5 :6,
                                6.9 :6,
                                '5' :5,
                                9.6 :9,     #because auto_convert = truncate : int(9.*) = 9
                            },
                            testValue_err = [
                                4, 10, 100,
                                True, False,
                                '4',
                                'r', None,
                                'True',
                            ]
                    )
                _test_str_empty_ = _test_str_empty_mnp()

            a = A()
            me.assertEquals( len( Messager._messages), 0 )
            me.assert_all_attributes_unset( a, [ 'm', 'n', 'p', 'mood', 'justanything' ])
            ALL = { A.__name__: A }
            test( ALL)

        def test_default_value0_ok( me):
            dv = 13
            class A( StaticStruct):
                m            = Number( default_value=dv, auto_convert=False )
                n_autoconvert= Number( default_value=str(dv) )   #auto_convert
            a = A()
            me.assertEquals( len( Messager._messages), 0 )
            me.assertEquals( a.m, dv)
            me.assertEquals( a.n_autoconvert, dv)

        def test_default_value1_err( me):
            def f():
                class A( StaticStruct):
                    m = Number(
                                default_value ='boza'   #wrong
                                )
            me.assertRaises( ValueError, f)

    class t_Bool( t_Base):
        def test_set_value( me):
            class Bza: pass
            class Zero:
                def __nonzero__( me): return False
            class A( StaticStruct):
                m = Bool( auto_convert=False,)
                m.autotester(
                        testValue_ok = {
                            True:True, False:False,
                        },
                        testValue_err = [
                            1,0,
                            'False', 'True',
                            1.0,
                            5,
                            None,
                            'anything',
                        ]
                    )

                n = Bool(   #auto_convert=True,
                        )
                n.autotester(
                        testValue_ok = {
                            'False': False, 'True': True,
                            1: True, 0: False,
                            5: True,
                            -4.7: True,
                            None: False,
                            'anythin': False,
                            Bza: True,
                            Bza(): True,
                            Zero(): False,
                        },
                        testValue_err = [ ],    #what ? all is bool()'able
                    )
                _test_str_empty_ = _test_str_empty_mnp(['m','n'])
            a = A()
            me.assertEquals( len( Messager._messages), 0 )
            ALL = { A.__name__: A }
            test( ALL)

    class t_Dict( t_Base):
        DICT = {'b1': 'boza 1', 'b2': 'boza2' }
        def test_set_value( me):
            class A( StaticStruct):
                m = AKeyFromDict( me.DICT, dictname = 'DICT',
                        default_value= 'b1',
                        use_reverse = False,
                        auto_convert= False,
                    )
                n = AKeyFromDict( me.DICT, dictname = 'DICT',
                        default_value= 'b2',
                        use_reverse = True,
                        auto_convert= False,
                    )
                p = AKeyFromDict( me.DICT, dictname = 'DICT',
                        default_value= 'b2',
                        use_reverse = AKeyFromDict.REVERSE_KEY_AND_VALUE,
                        auto_convert= False,
                    )
                _test_str_empty_ = """\
A(
    m = 'b1'
    n = 'b2'
    p = 'b2'
)"""
            me.assertEquals( len( Messager._messages), 0 )

            ALL = { A.__name__: A }
            test( ALL)
            #print A.m.dict
            #print A.n.StaticType_alt.reverse
            a = A()
            set = me.set
            me.assert_set_get( a, 'm', 'b1', 'b1' )
            me.assertRaises( ValueError, set(a,'m', 'anyth' ) )
            me.assertRaises( ValueError, set(a,'m', 'b1 ' ) )

            me.assert_set_get( a, 'n', 'b1', 'b1' )
            me.assertRaises( ValueError, set(a,'n', 'bozaaaaa' ) )
            me.assertRaises( ValueError, set(a,'n', 'b1 ' ) )

            me.assert_set_get( a, 'n_alt', 'boza2', )
            me.assertEquals(   a.n, 'b2')

            me.assert_set_get( a, 'p_alt', 'b1: boza 1', )
            me.assertEquals(   a.p, 'b1')

        def test_wrong_default( me):
            def f():
                class A( StaticStruct):
                    n = AKeyFromDict( me.DICT, dictname = 'DICT',
                            default_value= 'bzo',       #wrong
                        )
            me.assertRaises( ValueError, f)

        def test_wrong_dict_reverse( me):
            DICT2 = me.DICT.copy()
            DICT2[ 'b3'] = DICT2.values()[0]    ##wrong - duplicate reverse lookup
            class A( StaticStruct):
                n = AKeyFromDict( DICT2, dictname = 'DICT2',
                        default_value= 'b2',
                        use_reverse= True,
                    )
            me.assertEquals( len( Messager._messages), 1 )

    class t_Text( t_Base):
        def test_set_value( me):
            class Bza:
                txt = 'edna boza'
                def __str__( me): return me.txt
            bza = Bza()
            class A( StaticStruct):
                m = Text( auto_convert=False, )
                m.autotester(
                        testValue_ok = [
                            'anything',
                        ],
                        testValue_err = [
                            True, False,
                            1, 0,
                            1.0,
                            5,
                            None,
                            Bza, bza,
                        ]
                    )
                n = Text(   #auto_convert=True,
                        )
                n.autotester(
                        testValue_ok = {
                            'anything': 'anything',
                            'False': 'False', 'True': 'True',
                            1: '1', 0: '0',
                            5: '5',
                            -4.7: '-4.7',
                            None: 'None',
                            Bza: str(Bza),
                            bza: Bza.txt,
                        },
                        testValue_err = [ ],    #what ? all is str()'able
                    )
                p = Text(   #auto_convert=True,
                        min_size=3,
                        max_size=5,
                        )
                p.autotester(
                        testValue_ok = {
                            '123'   : '123',
                            '1234'  : '1234',
                            'abcde' : 'abcde',
                            12345   : '12345',
                        },
                        testValue_err = [
                            '12',
                            'abcdef',
                            123456,
                        ],
                    )
                _test_str_empty_ = _test_str_empty_mnp()

            a = A()
            me.assertEquals( len( Messager._messages), 0 )
            ALL = { A.__name__: A }
            test( ALL)


    import sys
    #config.notSetYet = None
    unittest.TestProgram( argv=sys.argv[:1] + [ '-v'] + sys.argv[1:] )

# vim:ts=4:sw=4:expandtab
