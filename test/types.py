#$Id$

from static_type.types.base import *
from static_type.types.base import _NONE
from test_base import test, _test_Base, _test_str_empty_mnp

if 0:
    class Number( StaticType):
        def __init__( me, type=int, **kargs):
            StaticType.__init__( me, type, **kargs)
    class Text( StaticType):
        def __init__( me, **kargs):
            StaticType.__init__( me, str, **kargs)
else:
    from static_type.types.atomary  import Number, Text
from static_type.types.sequence import Sequence
from static_type.types.indexall import build_order

import unittest
class t_Base( _test_Base, unittest.TestCase): pass

class t_Meta( t_Base):
    class Base( StaticStruct):
        #no default_value's
        Name = Text( meta=True, auto_convert =False)
        Age  = Number( meta=True)
        Gen  = Text( meta=True)
        mood = Text( auto_convert= False )
        _test_str_empty_ = _test_str_empty_mnp(
                                1 and [ 'Name', 'Age', 'Gen', 'mood']   #order
                                or ['Age', 'Gen', 'Name', 'mood'],      #noorder
                            'Base')

    def test0_base( me):
        a = me.Base()
        me.assertEquals( len( Messager._messages), 0 )

        me.assert_all_attributes_unset( a, [ 'Name', 'Age', 'Gen', 'mood', 'justanything' ] )
        me.assert_str( a, a._test_str_empty_ )

        #can set all defined attributes, meta or not, if not preset as meta in class
        for atr in [ 'Name', 'Age', 'Gen', 'mood', ]:
            setattr( a, atr, '1')
        me.assertEquals( a.Age, 1)
        for atr in [ 'Name', 'Gen', 'mood', ]:
            me.assertEquals( getattr( a, atr), '1')
        #can set only defined attributes
        me.assertRaises( AttributeError, me.set( a, 'something', 2))

    def test_meta0_ok( me):
        class B( me.Base):
            Name = 'tyutyu'
            Age  = 12
            Gen  = 'alala'

        me.assertEquals( len( Messager._messages), 0 )
        a = B()
        me.assert_str( a, """\
B(
    Age = 12
    Gen = 'alala'
    Name = 'tyutyu'
    mood = <not-set-yet>
)""")

        #can not set instance attribute if preset as meta in class
        me.assertRaises( AttributeError, me.set( a, 'Name', 'ime'))

    def test_meta1_miss( me):
        class B( me.Base):
            Name = 'uiouio'
            Age  = 12
            #Gen  = Text( meta=True)    intentional omission
        me.assertEquals( Messager._messages, [ """! warning: 'B': missing value of 'Gen'""" ] )
        a = B()
        me.assert_str( a, """\
B(
    Age = 12
    Gen = <not-set-yet>
    Name = 'uiouio'
    mood = <not-set-yet>
)""")

    def test_meta2_type( me):
        class B( me.Base):
            Name = 1    # intentional error
            Age  = 12
            Gen  = 1    # ok, auto_convert

        me.assertEquals( Messager._messages, [ '''\
!! ERROR: 'B': wrong value of 'Name' = 1
\t set type <type 'str'> with value 1 of type <type 'int'>''' ] )

        a = B()
        me.assert_str( a, """\
B(
    Age = 12
    Gen = 1
    Name = 1
    mood = <not-set-yet>
)""")


#########################

class t_Readonly( t_Base):
    class A( StaticStruct):
        value = 3
        m = Number( )
        n = Number( readonly=True, default_value = 23)
    def test_set( me):
        a = me.A()
        a.m = 1
        me.assertEquals( a.m, 1)
        me.assertRaises( AttributeError, me.set( a, 'n', 2))
        me.assertEquals( a.n, 23)

class t_Optional( t_Base):
    class A( StaticStruct):
        value = 3
        m = Number( optional=False)
        n = Number( optional='off', default_value=value )
        p = Number( optional='on')
        #_test_str_empty_ = _test_str_empty_mnp()
    value = A.value
    m_on = StaticType.OptionalitySwitch.slot_outside_StaticType( 'm')
    n_on = StaticType.OptionalitySwitch.slot_outside_StaticType( 'n')
    p_on = StaticType.OptionalitySwitch.slot_outside_StaticType( 'p')

    def setUp( me):
        t_Base.setUp( me)
        me.a = a = me.A()
        me.assertEquals( len( Messager._messages), 0 )

    def test0( me):
        a = me.a; value = me.value
        #me.assert_str( a, me.A._test_str_empty_ )
        me.assertRaises( AttributeError, lambda: getattr( a, me.m_on) )
        me.assertEquals( getattr( a, me.n_on), False)
        me.assertEquals( getattr( a, me.p_on), True )

        me.assert_set_get( a, 'p', value )
        me.assert_set_get( a, me.p_on, False )
        me.assert_set_get( a, me.p_on, True )
        me.assertEquals( a.p, value)

    def setup1( me):
        a = me.a
        n_on = me.n_on
        me.assertEquals( getattr( a, n_on), False)
        return a, n_on, me.value


    def test_get_off_error( me):
        a,n_on,value = me.setup1()
        StaticType.OPTIONALOFF_GET_IS = 'error'
        me.assertRaises( StaticType.OptionalOffError, lambda: a.n)
        me.assertEquals( getattr( a, n_on), False)

    def test_get_off_none( me):
        a,n_on,value = me.setup1()
        StaticType.OPTIONALOFF_GET_IS = None
        me.assertEquals( a.n, value )
        me.assertEquals( getattr( a, n_on), False)

    def test_get_off_turnon( me):
        a,n_on,value = me.setup1()
        StaticType.OPTIONALOFF_GET_IS = 'turnon'
        me.assertEquals( a.n, value )
        me.assertEquals( getattr( a, n_on), True)


    def test_set_off_error( me):
        a,n_on,value = me.setup1()
        StaticType.OPTIONALOFF_SET_IS_ERROR = True
        me.assertRaises( StaticType.OptionalOffError, lambda: setattr( a, 'n', value+1) )
        me.assertEquals( getattr( a, n_on), False)
        me.assertEquals( a.n, value )

    def test_set_off_turnon( me):
        a,n_on,value = me.setup1()
        StaticType.OPTIONALOFF_SET_IS_ERROR = False
        value += 1
        a.n = value
        me.assertEquals( getattr( a, n_on), True)
        me.assertEquals( a.n, value )


######

class t_Struct( t_Base):
    def test_inheritance1( me, res_only =False):
        class A1( StaticStruct):
            i = Number( meta=True)
            j = Number( type=float, default_value= 5)
            class B1( StaticStruct):
                m = Number( type=float, default_value= 4)
            p = SubStruct( B1, auto_set=False)
            q = SubStruct( B1, auto_set=True) #default
        if res_only: return A1

        a1 = A1()
        me.assert_all_attributes_unset( a1, ['p', 'i'] )
        me.assertEquals( a1.q.m, 4)
        #print a1
        a1.i = 3
        #for r in a1.getStaticTypesFlat( pfx='a1', obj=a1, meta =True):
        #    print r

    def test_inheritance2( me):
        def z(a): return SubStruct(a)
        A1 = me.test_inheritance1( res_only =True)
        class A2( A1):
            i = 14
            bozers = z(A1.B1)
            class C1( StaticStruct):
                class D1( StaticStruct):
                    t = z(A1.B1)
                D1 = z(D1)
            cozers = z(C1)

        a2 = A2()

        res = [ 'i', 'j',
                #'p.m',
                'q.m',
                'bozers.m',
                'cozers.D1.t.m',
            ]
        if config.STRUCT_AUTO_INSTANTIATE:
            res += [ 'B1.m', 'C1.D1.t.m', ]

        rez = dict( [ ('a2.'+a,None) for a in res] )
        for r in a2.getStaticTypesFlat( pfx='a2', obj=a2, meta =True, non_atomary=False):
            print r.__str__( obj=False)
            del rez[ r.fullname ]
        me.assertEquals( rez, {})


class B1( StaticStruct):
    m = Number( type=float, default_value= 4)
class C1( StaticStruct):
    m = Number( type=float, default_value= 4)
    n = Sequence( B1, min_size=2 )

class Dodo( list):
    def dodo( me, current, visitor):
        c = current
        fullname = visitor.fullname()
        yet = c.obj is config.notSetYet and ' '+str(c.obj) or ''
        print fullname, c.typ, c.obj is config.notSetYet and ' '+str(_NONE) or ''   #for the output-diff
        me.append( fullname+yet)

def str2lst( a): return a.strip().split('\n')

class t_Flat( t_Base):
    def assert_walk( me, a, expect =None, **kargs):
        A = a.__class__
        if expect is None: expect = str2lst( A._expect)
        result = node_names = Dodo()
        v = StaticType.Visitor4getFlat( doer=node_names.dodo, only_if_obj =True, **kargs)
        v.use( typ=A, name='a', obj=a)
        if node_names != expect:
            import difflib
            #if isinstance( h1, str): h1 = h1.splitlines(1)
            #if isinstance( h2, str): h2 = h2.splitlines(1)
            differ = difflib.context_diff # or difflib.unified_diff
            df = '\n'.join( differ( result, expect, 'result', 'expect') )
            me.failUnless( result == expect, 'result != expect\n'+df)
        return expect

    assert not Messager._messages

    class A1( StaticStruct):
        j = Number( type=float, default_value= 5)
        i = Number( meta=True)
        k = Text()
        z = B1          #near same as q
        p = SubStruct( B1, auto_set=False)
        q = SubStruct( B1, auto_set=True)
        _expect = ("""\
a
a.j
a.i
a.k %(notSetYet)s
"""+ (config.STRUCT_AUTO_INSTANTIATE and """\
a.z
a.z.m
""" or '') + """\
a.p %(notSetYet)s
a.q
a.q.m
""") % config.__dict__

        _non_atomary = ("""
a
"""+ (config.STRUCT_AUTO_INSTANTIATE and """\
a.z
""" or '') + """\
a.p %(notSetYet)s
a.q
""" ) % config.__dict__

    assert not Messager._messages

    def test_A1( me):
        A = me.A1
        a = A()
        me.assert_all_attributes_unset( a, ['p', 'i', 'k'] )
        me.assertEquals( a.j  , 5)
        me.assertEquals( a.q.m, 4)
        a.i = 3

        expect = me.assert_walk( a)

        expect= [ n for n in expect if n != 'a.i' ]
        me.assert_walk( a, expect, meta=False)

        expect= [ n for n in expect if n not in str2lst( A._non_atomary) ]
        me.assert_walk( a, expect, meta=False, non_atomary=False)


    class A2(A1):
        r = Sequence( int, min_size=2 )
        s = Sequence( Number(), min_size=2 )
        t = Sequence( B1, min_size=2 )
        u = Sequence( C1, min_size=1 )
        i = 2
        _expect = """
a.r
a.r.items.0
a.r.items.1
a.s
a.s.items.0 %(notSetYet)s
a.s.items.1 %(notSetYet)s
a.t
a.t.items.0
a.t.items.0.m
a.t.items.1
a.t.items.1.m
a.u
a.u.items.0
a.u.items.0.m
a.u.items.0.n
a.u.items.0.n.items.0
a.u.items.0.n.items.0.m
a.u.items.0.n.items.1
a.u.items.0.n.items.1.m
""" % config.__dict__
        _non_atomary = """
a.r
a.s
a.t
a.u
a.t.items.0
a.t.items.1
a.u.items.0
a.u.items.0.n
a.u.items.0.n.items.0
a.u.items.0.n.items.1
"""
    assert not Messager._messages

    A2._expect = A1._expect.strip() + A2._expect
    A2._non_atomary = A1._non_atomary.strip() + A2._non_atomary


    def test_A2( me):
        A = me.A2
        a = A()
        me.assert_all_attributes_unset( a, ['p', 'k'] )
        me.assertEquals( a.j  , 5)
        me.assertEquals( a.q.m, 4)

        me.assertEquals( a.r[0],0)
        me.assertEquals( a.s[0],config.notSetYet)
        me.assertEquals( a.t[0].m, 4)
        me.assertEquals( a.u[0].m, 4)
        me.assertEquals( a.u[0].n[1].m, 4)

        #for r in a1.getStaticTypesFlat( pfx='a1', obj=a1, meta =True):
        #    print r

        expect = me.assert_walk( a)

        expect= [ n for n in expect if n not in str2lst( A._non_atomary) ]
        me.assert_walk( a, expect, non_atomary=False)


    class A3( StaticStruct):
        j = Number( type=float, default_value= 5)
        k = Text()
        l = Number( default_value=11, optional='on' )
        n = Number( default_value=22, optional='off')
        q = SubStruct( B1, auto_set=True)
        _expect_n_value = (StaticType.OPTIONALOFF_GET_IS != 'turnon'
                            and StaticType.OPTIONALOFF_GET_IS
                                and ' '+str(config.notSetYet)
                                or '' )
        notSetYet = config.notSetYet
        _expect = """
a
a.j
a.k %(notSetYet)s
a.l__on
a.l
a.n__on
a.n%(_expect_n_value)s
a.q
a.q.m
""" % locals()
    assert not Messager._messages

    def test_A3( me):
        A = me.A3
        a = A()
        #me.assert_all_attributes_unset( a, ['p', 'i', 'k', 'n'] )
        me.assertEquals( a.j  , 5)
        me.assertEquals( a.q.m, 4)

        expect = me.assert_walk( a)

        expect= [ n for n in expect if not '__on' in n ]
        me.assert_walk( a, expect, optional_switch=False)

        expect= [ n for n in expect if 'a.n' not in n ]
        me.assert_walk( a, expect, optional_switch=False, optional_off=False)


if __name__ == '__main__':
    build_order( locals(), __file__, with_classes=True)     #non-dynamic-made classes only
    import sys
#    config.notSetYet = None ##this only breaks above '...' % config.__dict__
    unittest.TestProgram( argv=sys.argv[:1] + [ '-v'] + sys.argv[1:] )

# vim:ts=4:sw=4:expandtab
