#$Id$

from static_type.types.base import _NONE, StaticType, Syncer, Sizer, config
#above static_type.types. because of test.test_base
import sys as _sys

class Attr2Item( object):
    ALLOW_AUTO_RESIZE = False
    def __init__( me, host):
        object.__setattr__( me, 'host', host)
        #object.__setattr__( me, 'validator', validator)
    def __setattr__( me, name, value):
        try:
            i = int( name)
        except (ValueError, TypeError), e:
            raise AttributeError, e

        #if me.validator:
        #   value = me.validator( value, name=name)

        host = me.host
        try:
            host[ i] = value     #setitem
        except IndexError, e:
            if not me.ALLOW_AUTO_RESIZE:
                raise AttributeError, e
            #print i#, host._parent
            host._resize( i+1, down=False )
            host[ i] = value

    def __getattr__( me, name):
        try:
            i = int( name)
        except (ValueError, TypeError), e:
            raise AttributeError, e
        host = me.host

        try:
            return host[ i ]
        except IndexError, e:
            if not me.ALLOW_AUTO_RESIZE:
                raise AttributeError, e
            host._resize( i+1, down=False )
            return host[ i ]

_locals = { '__builtins__': None }

class SeqContainer( list):
    """ list which:
        x.items.5 is equivalent to x[5] - item-access via attr-access
        x._incr/x._decr/x._resize sizing methods
        x.incr / x.decr properties = assigning anything to them changes size by 1
        min/max size functionality
        sync_size functionality
    use:
        for each needed instance, make a subclass and
        set ._parent and ._slave2resize, and then use that as instance's type.
    warning:
        constructor of sequence will sync its slaves, if any.
        -> first access to a sequence may (lazy) call a constructor -> sync
    """
    __slots__ = [ 'items', '_sync_lock', '_slave2resize', '_slave2setitem' ]
    _parent = None    #Sequence's instance!
    def __init__( me, value =_NONE, *a, **kargs_ignore):
        me._sync_lock = False
        parent = me.__class__._parent
        me.items = Attr2Item( me)
        me._slave2resize = ()
        me._slave2setitem = None
        size = parent.min
        if value is _NONE:
            value = ()
            size = parent.default_size or parent.min
        elif isinstance( value, str):
            try:
                value = eval( value, _locals, _locals )       #dangerous?
            except (ValueError, TypeError): raise
            except:
                e = _sys.exc_info()[1]
                e_type = e.__class__.__name__
                raise ValueError, '%(value)s [%(e_type)s: %(e)s]' % locals()

        list.__init__( me, value)
        if not me._resize( size, down=False ):
            me._sync()

    str = staticmethod( str)
    def __str__( me):
        str = me.str
        return me.__class__._parent.name +': '+ ', '.join( [str(s) for s in me])
    def __str_short__( me):
        str = me.str
        return '[ '+ ', '.join( [str(s) for s in me]) + ' ]'

    #def test_slice_size( slic, l =range(10)):
    #    begin, end, step = slic.indices(len(l))
    #    s_l = max(0, (end -begin + (step>0 and -1 or +1) ) / step +1)
    #    assert len( l[slic]) == s_l

    def __setitem__( me, key, value):
        #print 'setitem', me, key, value
        parent = me.__class__._parent
        item_validator = parent._item_validator
        delta_sz = 0
        if isinstance( key, slice):
            l = len(me)
            begin, end, step = key.indices(l)
            slice_sz = max(0, (end -begin + (step>0 and -1 or +1) ) / step +1)
            delta_sz = len(value) - slice_sz
            #print 'delta_sz', delta_sz
            new_sz = l + delta_sz
            lmax = parent.max
            if lmax is not None and new_sz > lmax:
                raise ValueError, 'reached max size %r' % lmax
            lmin = parent.min
            if new_sz < lmin:
                raise ValueError, 'reached min size %r' % lmin

            value = parent.validate_typecheck( value)
            if item_validator:
                value = [ item_validator( v) for v in value ]
        else:
            if item_validator:
                value = item_validator( value, name=str(key))
            if parent.OPTIONALOFF_SETITEM_IS_TURNON and me._slave2setitem:
                me._slave2setitem()
        try:
            list.__setitem__( me, key, value)
        except (ValueError, TypeError), e:
            raise AttributeError, e     #???
        if delta_sz:
            me._sync()

    def __setslice__( me, i,j, value):
        me[ max(0, i):max(0, j):] = value
    def __delslice__( me, i,j):
        me[ max(0, i):max(0, j):] = ()

    def _incr( me, *args_ignore):
        parent = me.__class__._parent
        max = parent.max
        if max is not None and len( me) >= max:
            raise ValueError, 'reached max size %r' % max
        me.append( parent.item_type() )
        #me._sync()

    def _decr( me, *args_ignore):
        min = me.__class__._parent.min
        if len( me) <= min:
            raise ValueError, 'reached min size %r' % min
        me.pop( -1)
        #me._sync()

    incr = property( lambda *a,**k: config.notSetYet, _incr )
    decr = property( lambda *a,**k: config.notSetYet, _decr )

    def _resize( me, sz, up =True, down =True):
        """silently fit sz into min..max"""
        #print 'resize', sz, up, down, me
        parent = me.__class__._parent
        if parent.max is not None:
            sz = min( sz, parent.max)
        sz = max( sz, parent.min)
        #print '>',sz
        l = len( me)
        if sz>l:
            if up:
                item_type = parent.item_type
                r = [ item_type() for i in xrange( sz-l)]     #fill up to sz
                me.extend( r )
                #me._sync() - auto by extend
                return True
        elif sz<l and down:
            #print 'down', sz, l, me._sync_lock
            del me[ sz:]
            #me._sync() auto by del
            return True
        return False

    def _sync( me):
        if not me._sync_lock:   #break circular dependency
            #print 'sync', me
            try:
                me._sync_lock = True
                l = len( me)
                for f in me._slave2resize: f( l)
                #or direct:
                #parent = me.__class__._parent
                #parent._sync(l) - need to be obj-bound
            finally:
                me._sync_lock = False

    _sync_after = [     #XXX all these must check min/max !
        'append', 'insert', 'extend', '__iadd__',
        'pop', 'remove',
        '__delitem__',
        #'__setitem__', no, defined above
        #'__setslice__',     #slices do not go to setitem
        #'__delslice__',     #slices do not go to delitem
        ##'reverse', 'sort' do not change size
        #'_resize', '_incr', '_decr',
    ]
    if 10:
        # generate overloading methods for all of them:
        for f in _sync_after:
            _locals = locals()
            exec( """def %(f)s( me, *a,**k):
                    #print '%(f)s', me
                    r = list.%(f)s( me, *a,**k)
                    me._sync()
                    return r """ % _locals, _locals, _locals )
    #pickleing
    def __reduce__( me): return (list, (list(me),) )


class Sequence( StaticType, Syncer, Sizer):
    Attr2Item = Attr2Item           #have it here
    non_atomary = True
    OPTIONALOFF_SETITEM_IS_TURNON = True
    def __init__( me, type =int, item_type =None,
                    sync_size_masters =None,    # list-of-other vectors
                    sync_size_slaves  =None,    # list-of-other vectors
                    **kargs):
        item_type = StaticType.makeStaticType( item_type or type )
        item_type.name = 'item'                         #??
        me.item_type = item_type
        me._item_validator = item_type._validate

        kargs = Sizer.__init__( me, **kargs)

        class Container_type( SeqContainer):
            __slots__ = ()
            _parent = me
        me.container_type = Container_type

        if sync_size_slaves is not None:
            if isinstance( sync_size_slaves, Syncer.DualList):
                sync_size_slaves.append( me)
            me._sync_slaves = sync_size_slaves
        if sync_size_masters is not None:
            if isinstance( sync_size_masters, Syncer.DualList):
                sync_size_masters.append( me)
            me._sync_masters = sync_size_masters

        StaticType.__init__( me, Container_type, default_value= Container_type,
                    typ_matcher= lambda value,typ: isinstance( value, (tuple,list)),
                    **kargs )

    # _sync_slaves is stored in container's instance, and regenerated for every
    #       container __set__ (and also default_value's lazy get) - which is rare op
    # it can be made once per parent obj -- see 2nd alternative sync_get_slave_func,
    #   but where to store it, and using (frequent op) it is slower
    # also, it can be moved out of container instance, but then the very initial
    #   container._sync() will try to access inexisting (not-set-yet) containers of the slaves,
    #   which will autocreate, and if Dual/2way, will try access the (not-set-yet) originator -
    #   which is an infinite recursion.

    def _setattr_props( me, obj, name, value ):
        StaticType._setattr_props( me, obj, name, value )
        #XXX what if value is notSetYet, i.e. unset?
        me.sync_setup( obj, do_sync=True)    #after actual setattr

    def _slavesync( me, obj, sz):
        ##this to auto-enable/disable optionals depending on size
        if 0:
            if me.optional:
                me.optional.__set__( obj, bool(sz) )

        me.__get__( obj)._resize( sz)

    def sync_get_slave_func( me, obj):
        return lambda sz: me._slavesync( obj, sz)
        #return getattr( obj, me.name)._resize
        ##this allows the _slave2resize list below to be made once per obj
        #return lambda value: getattr( obj, me.name)._resize( value)
    def sync_setup( me, obj, do_sync =False):
        'pass actual instance, after all sync_inits but before usage'
        c = getattr( obj, me.name)
        if me._sync_slaves:
            c._slave2resize = [ typ.sync_get_slave_func( obj)
                                for typ in me._sync_slaves ]   #other Syncer/Type's
            if do_sync: c._sync()
        if me.optional:
            c._slave2setitem = lambda : me.optional.__set__( obj, True)

    def _validate( me, value, obj =None, **kargs_ignore):
        value = me.validate_typecheck( value)
        Sizer.validate( me, value)
        item_validator = me._item_validator
        #print me.name, item_validator
        if item_validator:
            val = []
            for v in value:   #XXX notSetYet bypasses validate!
                if v not in (config.notSetYet, _NONE): v = item_validator( v)
                val.append(v)
            value = val
        typ = me.container_type
        if not isinstance( value, typ): value = typ( value )
        value = me.validate_validator( value, obj)
        return value

    def walk( me, visitor ):
        obj = visitor.current.obj
        i_typ = visitor.current.typ.item_type
        use = visitor.use
        if obj is not config.notSetYet:
            for i in xrange( len( obj)):
                nm = 'items.%s' % i
                o = obj[i]
                use( i_typ, nm, o )
        else:
            use( i_typ, 'items', obj )

    def __str__( me):
        m = me.typ
        me.typ = me.item_type
        try:
            r = StaticType.__str__( me)
        finally:
            me.typ = m
        return r + Sizer.__str__( me)
    def description( me):
        return StaticType.description(me) + Sizer.__str__( me)

    if 0:
        def _validator_instance( me, v, **kargs_ignore):
            if not isinstance( v, me.item_type):
                raise TypeError, me.TYPEERROR( me.item_type, v)
            #do not change it
            return v
        _item_validator = _validator_instance

        def _validator_subclass( me, v, **kargs_ignore):
            if not issubclass( v, me.item_type):
                raise TypeError, me.TYPEERROR( me.item_type, v)
            #do not change it
            return v


        def z__get__( me, obj, klas =None):
            if obj is None: return me
            value = StaticType.__get__( me, obj, klas )
            return me.size_sync( value)

    def size( me): raise NotImplemented

#################
#################

if __name__ == '__main__':
    import unittest
    from static_type.types.base import StaticStruct, Messager
    from static_type.test.test_base import test, _test_Base
    from atomary import Number, Text
    from svd_util.attr import set_attrib
    class t_Base( _test_Base, unittest.TestCase): pass

    class t_Sequence( t_Base):
        def __init__( me, *a,**k):
            t_Base.__init__( me, *a,**k)
            if config.notSetYet is None:
                class ERRORvalue: pass
            else:
                ERRORvalue = None
            me.ERRORvalue = ERRORvalue

        def test_0_make0( me):
            class A( StaticStruct):
                m = Sequence( item_type=int, )                  #always present - empty
                n = Sequence( item_type=int, min_size=3,)
                p = Sequence( item_type=Number(), min_size=3,)
                _test_str_empty_ = """\
A(
    m = []
    n = [0, 0, 0]
    p = """ + str( 3*[config.notSetYet]) + """
)"""
            a = A()
            me.assertEquals( len( Messager._messages), 0 )
            me.assert_str( a, a._test_str_empty_)
            me.assertEquals( a.n[0], 0)
            me.assertEquals( a.p[0], config.notSetYet)                 #???

        def test_0_make( me):
            class Bza:
                txt = 'edna boza'
                def __str__( me): return me.txt
            bza = Bza()
            TestItem = StaticType.Test.TestItem

            atomary_testValue_err = [
                            True, False,
                            1, 0,
                            1.0,
                            5,
                            me.ERRORvalue,
                            Bza, bza,
                        ]

            class A( StaticStruct):
                ok4 = [ 0, 1, 55, 2, ]
                m = Sequence( item_type=int,    #default = items_autoconverted
                        auto_convert=False,     #whole unconverted
                    )
                m.autotester(
                        testValue_ok = [
                            ok4,
                            TestItem( tuple(ok4), ok4),
                            TestItem( ok4[:1]+[str(ok4[1])]+ok4[2:], ok4 ),
                            ],
                        testValue_err = atomary_testValue_err + [
                            str(ok4),                   #no autoconvert whole
                            xrange( 4),                 #no autoconvert whole
                            [ 'anything1', 1, ],        #itemtype
                            [ 1, 2, me.ERRORvalue, ],            #itemtype
                            TestItem( 'some string', TypeError) ,
                        ]
                    )
                n = Sequence( item_type=int,
                        auto_convert=True,    #whole converted
                    )
                n.autotester(
                        testValue_ok = [
                            ok4,
                            TestItem( tuple(ok4), ok4),
                            TestItem( str(ok4), ok4),
                            TestItem( xrange( 4), [0,1,2,3] ),
                        ],
                        testValue_err = atomary_testValue_err + [
                            TestItem( 'some string2', ValueError) ,
                        ],
                    )
                p = Sequence( item_type=int,
                        #auto_convert=True,
                        min_size=3,
                        max_size=5,
                    )
                p.autotester(
                        testValue_ok = [
                            [1,2,3],
                            TestItem( xrange( 4), [0,1,2,3] ),
                            [14,11,12,13,10],
                            TestItem( str( [4,1,2,3,]), [4,1,2,3] ),
                        ],
                        testValue_err = [
                            [1,],               #size
                            [1,2,3,4,5,6],      #size
                            [1,2,3,'a',me.ERRORvalue],   #itemtype
                        ],
                    )
                _test_str_empty_ = """\
A(
    m = []
    n = []
    p = [0, 0, 0]
)"""

            me.assertEquals( len( Messager._messages), 0 )
            return A

        def test_1_set_value_whole( me):
            A = me.test_0_make()
            a = A()
            ALL = { 'Sequence_set_value_whole': A}
            test( ALL)

        def test_2_size_0( me):
            A = me.test_0_make()
            a = A()
            ###### items
            v = 375
            def set_index( ix, value): a.m[ix] = value
            def get_index( ix): return getattr( a.m, str(ix))
            #outside size
            me.assertRaises( IndexError, set_index, 0, v)
            me.assertRaises( AttributeError, get_index, 0)

        def test_2_size_1( me):
            A = me.test_0_make()
            a = A()
            #no get first
            a.m._resize(1)
            me.assertEquals( len(a.m), 1)

        def test_2_size_2( me):
            A = me.test_0_make()
            a = A()
            #do get first
            q = a.m
            q._resize(2)
            me.assertEquals( len(q), 2)
            me.assertEquals( len(a.m), 2)
            a.m._resize(1)
            me.assertEquals( len(a.m), 1)

        def test_3_set_items( me):
            A = me.test_0_make()
            a = A()
            def set_index( ix, value): a.m[ix] = value
            def get_index( ix): return getattr( a.m, str(ix))

            #set via [ix]; check via [ix] and .items.ix
            v = 124
            a.m._resize(1)
            a.m[0] = v
            me.assert_set_get_item( a.m, 0, v)
            me.assertEquals( a.m[-1], v)
            #outside size
            me.assertRaises( IndexError, set_index, 1, v)
            me.assertRaises( IndexError, set_index, 4, v)

            #set via items
            def set_index2( ix, value): setattr( a.m.items, str(ix), value)
            v2 = 12
            set_index2( 0, v2)
            me.assertEquals( a.m[0], v2)

            me.assertRaises( AttributeError, set_index2, 1, v2) #outside

            #itemtype check
            me.assert_set_get_item( a.m, 0, '134', 134)    #ok - auto_converting item
            me.assertRaises( ValueError, set_index, 0, 'e')
            me.assertRaises( TypeError, set_index, 0, me.ERRORvalue)


        def test_3_sizes( me):
            A = me.test_0_make()
            a = A()

            #sizes
            vv = a.m[:]

            a.m._incr()
            me.assertEquals( len( a.m), len(vv)+1 )
            me.assertEquals( a.m, vv+[0] )

            a.m._decr()
            me.assertEquals( a.m, vv )

            a.m.incr = 'somethng'
            me.assertEquals( len( a.m), len(vv)+1 )
            a.m.incr = 4
            me.assertEquals( len( a.m), len(vv)+2 )
            a.m.decr = 4
            me.assertEquals( len( a.m), len(vv)+1 )

            def padd(v,sz): return vv+ [0]*(sz-len(v))
            sz = 10
            a.m._resize(sz)
            me.assertEquals( len( a.m), sz )
            me.assertEquals( a.m, padd( vv,sz))
            a.m._resize(1)
            me.assertEquals( len( a.m), 1 )

            #sizes min/max
            vv = [ 3,7,2 ]
            a.p = vv
            a.p._resize( A.p.min-1)             #size<min - up to min
            me.assertEquals( a.p, vv )          #not changed
            a.p._resize( A.p.min)               #size<min
            me.assertEquals( a.p, vv )          #not changed
            sz = (A.p.min+A.p.max)/2
            a.p._resize( sz )                   #size in min..max
            me.assertEquals( a.p, padd( vv,sz))

            a.p._resize( A.p.max+1)             #size>max - down to max
            me.assertEquals( a.p, padd( vv, A.p.max) )

            #XXX must also test all the setitem, setslice etc

        def assert_set_get_item( me, seq, index, value, value_out =_NONE, types =True):
            if value_out is _NONE: value_out = value
            seq[ index] = value
            v = seq[ index]
            me.assertEquals( v, value_out)
            me.assertEquals( getattr( seq.items, str(index)), value_out)
            if types:
                me.assertEquals( type(v), type(value_out))

        def test_4_structitems( me):
            class B( StaticStruct):
                i = Number()
                n = Text()

            class A( StaticStruct):
                m = Sequence( item_type=B, )

            a = A()
            a.m._incr()
            #print a.m
            #print len(a.m), a.m, id(a.m), type(a.m), id(a.m)
            v = 4
            a.m[0].i = v
            me.assertEquals( a.m[0].i, v)
            a.m[0].n = 'ino'
            v = 14
            set_attrib( a, 'm.items.0.i', v)
            me.assertEquals( a.m[0].i, v)

        def test_5_syncsize_1( me):
            #""" warning! first access to (lazy-set) sequence will sync its slaves"""
            ll = 0
            class A( StaticStruct):
                m = Sequence( item_type=int,    min=ll )
                p = Sequence( item_type=str,    min=ll, sync_size_masters = [ m] )
            class B( StaticStruct):
                p = Sequence( item_type=str,    min=ll, )
                m = Sequence( item_type=float,  min=ll, sync_size_slaves = [ p] )

            def t(a):       #test: p is synced to m
                a.m._incr()
                me.assertEquals( len(a.m), ll+1)
                me.assertEquals( len(a.p), len(a.m))
                a.p._incr()
                me.assertEquals( len(a.p), len(a.m)+1)
                a.m._decr()
                me.assertEquals( len(a.p), len(a.m))

                a.m._resize(5)
                me.assertEquals( len(a.m), max(5,ll) )
                me.assertEquals( len(a.p), len(a.m) )

            a = A()
            t(a)
            b = B()
            t(b)

        def test_5_syncsize_dual( me):
            ll = 0
            class C( StaticStruct):
                s = Sequence.DualList()
                p = Sequence( item_type=str,    min=ll, sync_size_masters = s )
                m = Sequence( item_type=float,  min=ll, sync_size_masters = s )
            a = C()

            a.m._incr()
            me.assertEquals( len(a.p), len(a.m))
            me.assertEquals( len(a.m), ll+1)
            a.p._incr()
            me.assertEquals( len(a.p), len(a.m))
            me.assertEquals( len(a.p), ll+2)
            a.m._decr()
            me.assertEquals( len(a.p), len(a.m))
            me.assertEquals( len(a.m), ll+1)
            a.p._decr()
            me.assertEquals( len(a.p), len(a.m))
            me.assertEquals( len(a.m), ll)

            a.m._resize(7)
            me.assertEquals( len(a.m), max(7,ll) )
            me.assertEquals( len(a.p), len(a.m) )
            a.m._resize(5)
            me.assertEquals( len(a.m), max(5,ll) )
            me.assertEquals( len(a.p), len(a.m) )

            #append
            ll = len(a.m)
            a.m.append( 5.5 )
            me.assertEquals( len(a.m), ll+1 )
            me.assertEquals( len(a.p), len(a.m) )

            #extend
            ll = len(a.m)
            vl = [6.5, 7, 8]
            a.m.extend( vl)
            me.assertEquals( len(a.m), ll+len(vl) )
            me.assertEquals( len(a.p), len(a.m) )

            #setslice
            vl = [9.5, 8.5]
            ll = len(a.m)
            a.m[ 1:5] = vl
            me.assertEquals( len(a.m), ll+len(vl)-4 )
            me.assertEquals( len(a.p), len(a.m) )

            #delitem
            ll = len(a.m)
            del a.m[ 1]
            me.assertEquals( len(a.m), ll-1 )
            me.assertEquals( len(a.p), len(a.m) )

            #delslice
            del a.m[ 3:]
            me.assertEquals( len(a.m), 3 )
            me.assertEquals( len(a.p), len(a.m) )

            #pop
            ll = len(a.m)
            a.m.pop( 0)
            me.assertEquals( len(a.m), ll-1 )
            me.assertEquals( len(a.p), len(a.m) )

        def test_5_syncsize_number( me):
            ll = 1
            class C( StaticStruct):
                s = Sequence.DualList()
                n = Number()
                s.append( n)
                m = Sequence( item_type=float, min=ll, sync_size_masters = s )
                p = Sequence( item_type=str,   min=ll, sync_size_masters = s )

            a = C()

            a.m._incr()
            ll +=1
            me.assertEquals( len(a.p), ll)
            me.assertEquals( len(a.m), ll)
            me.assertEquals( a.n, ll)

            a.p._incr()
            ll += 1
            me.assertEquals( len(a.p), ll)
            me.assertEquals( len(a.m), ll)
            me.assertEquals( a.n, ll)
            ll= 5
            a.n = ll
            me.assertEquals( a.n, ll)
            me.assertEquals( len(a.m), ll)
            me.assertEquals( len(a.p), ll)

    import sys
    #config.notSetYet = None
    unittest.TestProgram( argv=sys.argv[:1] + [ '-v'] + sys.argv[1:] )

# vim:ts=4:sw=4:expandtab
