#$Id$
# -*- coding: cp1251 -*-

from static_type.types.base import StaticType, _NONE, StaticStruct, issubclass, Messager, config

class Test:
    _NONEl = [ config.notSetYet ]
    _testValue_ok  = _NONEl
    _testValue_err = _NONEl

    def __init__( me, victim, **kargs):
        me.victim = victim
        me._setup_testing( **kargs)

#### auto-testing
    def _setup_testing( me, testValue_ok  =_NONEl, testValue_err =_NONEl ):
        if testValue_ok is not me._NONEl:
            if not isinstance( testValue_ok, (tuple, list, dict)):
                testValue_ok = [ testValue_ok ]
            me._testValue_ok  = testValue_ok
        if testValue_err is not me._NONEl:
            if not isinstance( testValue_err, (tuple, list, dict)):
                testValue_err= [ testValue_err]
            me._testValue_err = testValue_err
    class TestItem( tuple ):
        """use instead of tuple in testValue_* lists"""
        def __new__( klas, *args):
            return tuple.__new__( klas, args)
    def get_testValue_ok( me, **kargs_ignore):
        return me._testValue_ok
    def get_testValue_err( me, **kargs_ignore):
        return me._testValue_err
    def test_inputs( me, obj, inputs, functor, name=''):
        if not name: name = me.victim.name
        for v in inputs:
            if v is not config.notSetYet:
                if isinstance( inputs, dict):
                    expect = inputs[v]
                else:
                    if isinstance( v, me.TestItem):
                        v,expect = v
                    else:
                        expect = functor.default_expect or v
                yield functor( obj, name, v), expect
StaticType.Test = Test

if 0:   #in all.py
    def test_print_ALL( name, ALL):
        print name, 'items: {'
        for av in ALL.iteritems():
            print '  %s = %s' % av
        print '}'

def test( ALL, verbosity =2 ):    #mainly for records
    #test_print_ALL( name, ALL)
    #print ALL.keys()

    import unittest
    import sys

    class SetAttr:
        default_expect = TypeError,ValueError
        def __init__( me, obj, name, value):
            me.obj = obj
            me.name = name
            me.value = value
        def __call__( me): return setattr( me.obj, me.name, me.value)
        def __str__( me):  return 'setattr %s=%r' % (me.name, me.value)

    class SetGetAttr( SetAttr):
        default_expect = None
        def __call__( me):
            obj = me.obj
            name = me.name
            setattr( obj, name, me.value)
            return getattr( obj, name)
        def __str__( me): return 'setattr/get %(name)s=%(value)r' % me.__dict__


    class Test_Record( unittest.TestCase):
        name = None
        factory = None
        def __str__( me):
            #why unittest._strclass is not a method...
            try:
                return "  %s (%s)" % (me._testMethodName, me.name or me.factory )
            except AttributeError:
                return "  %s (%s)" % (me._TestCase__testMethodName, me.name or me.factory )

        def test_ctor_OK( me, quiet =False):
            r = me.factory()
            if quiet: return r
            #if not quiet: print '\n ',r
            rstr = str(r)  #setup all
            try:
                str_empty = r._test_str_empty_
            except AttributeError:
                if not quiet: print ' ! no _test_str_empty_ for %s' % r.__class__.__name__
            else:
                me.assertEquals( rstr, str_empty.strip() )

            #def err_assign_to_a_record():  r.Parameters = 1
            #me.assertRaises( AttributeError, err_assign_to_a_record )
            def err_assign_extra_member(): r.alabalanica123454 = 1
            me.assertRaises( AttributeError, err_assign_extra_member )
            return r
        def dont_test_ctor__ERR_args( me):
            me.assertRaises( TypeError, me.factory, 1 )
            me.assertRaises( TypeError, me.factory, whateverNam='alabala' )

        def dirStaticTypes( me, obj):
            'yield parent-obj, local-name, typ  for all StaticTypes in hierarchy'

            for name,typ in obj._order_Statics( items=True):
                if issubclass( typ, StaticStruct):
                    obj1 = getattr( obj, name)
                    for obj1,name1,typ in me.dirStaticTypes( obj1):
                        yield obj1, name1,typ
                else:
                    if not typ.meta:
                        yield obj, name,typ

        experr = ('expect %(expect)s; got %(result)s:'+
                  '\n %(parent)s.%(name)s, %(typ)s\n %(func)s\n')

        def _test_set_value_OKERR( me, OK =True, title=''):
            parent = me.name
            r = me.test_ctor_OK( quiet=True)
            print
            functor = OK and SetGetAttr or SetAttr
            for obj,name,typ in me.dirStaticTypes( r):
                print ' %s.%s' % ( obj.__class__.__name__, typ)
                n = 0
                try:
                    tester = typ.tester
                except AttributeError:
                    tester = typ.Test( typ)
                inputs = (OK and tester.get_testValue_ok or tester.get_testValue_err)()
                #auto turn on
                if typ.optional and not typ.optional.__get__( obj):
                    typ.optional.__set__( obj, True)

                for func,expect in tester.test_inputs( obj, inputs, functor=functor):
                    n+=1
                    try:
                        result = func()
                    except:
                        e = result = sys.exc_info()[1]
                        if issubclass( expect, Exception) or isinstance( expect, tuple) and issubclass( expect[0], Exception):
                            #print '*******', e, expect
                            if isinstance( e, expect): continue
                            if isinstance( expect, tuple):
                                expect = ','.join( [p.__name__ for p in expect] )
                            else: expect = expect.__name__
                        result = result.__class__.__name__
                        experr = '\n' + title + me.experr % locals()
                        e.args = ((e.args and e.args[0] or '') + experr ,) + e.args[1:]
                        raise
                    else:
                        if expect != result:
                            raise AssertionError, (me.experr +title) % locals()
                if not n:
                    print ' ! no testValue_%s for %s' % ( OK and 'ok' or 'err', name)
            return r

        def test_set_value_OK( me, title=''):
            return me._test_set_value_OKERR()
        def test_set_value__ERR( me):
            return me._test_set_value_OKERR( OK=False)
            #test that errors do not change r ???

    def Test_Record_Factory( ctor, name =None):
        class ctorTest_Record( Test_Record):
            factory = ctor
        if name: ctorTest_Record.name = name
        return ctorTest_Record

    cases = [ unittest.defaultTestLoader.loadTestsFromTestCase(
                Test_Record_Factory( ctor,name=name) ) for name,ctor in ALL.iteritems()
                #case ) for case in namespace.itervalues() if issubclass( case, unittest.TestCase)
            ]
    s = unittest.TestSuite( cases)
    unittest.TextTestRunner( unittest.sys.stdout, verbosity=verbosity, descriptions=True, ).run( s )

class _test_Base:   #( unittest.TestCase):
    def setUp( me):
        Messager._test = True
        Messager._messages = []
        print
    def assert_str( me, obj, str_org):
        me.assertEquals( str(obj), str_org)
    def assert_set_get( me, obj, name, value, value_out =_NONE, types =True):
        if value_out is _NONE: value_out = value
        setattr( obj, name, value)
        v = getattr( obj, name)
        me.assertEquals( v, value_out)
        if types:
            me.assertEquals( type(v), type(value_out))
    def set( me, obj, name, value):
        return lambda: setattr( obj, name, value)
    def assert_all_attributes_unset( me, obj, attrs):
        #all unset attributes are AttributeError
        for atr in attrs:
            me.assertRaises( AttributeError, lambda : getattr( obj, atr))

def _test_str_empty_mnp( mnp =['m','n','p'], name='A', ):
    return name+'(\n'+ '\n'.join( ['    %s = <not-set-yet>' % a for a in mnp] ) + '\n)'

#if __name__ == '__main__':
#    import unittest
##    from test_base import _test_Base
#    class t_Base( _test_Base, unittest.TestCase): pass
#
#... class t_Meta( t_Base):
#
#    import sys
#    unittest.TestProgram( argv=sys.argv[:1] + [ '-v'] + sys.argv[1:] )

# vim:ts=4:sw=4:expandtab
