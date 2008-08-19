#$Id$

"""
 simplest StaticType container is:
   struct.StaticTypes = dict()
   but it is hard to access instance StaticType'd values in uniform way with names and types
 now:
   struct.StaticTypes = Descriptor4Container( Proxy4Container )
    *.StaticTypes.iterkeys gives (ordered) names
    instance.StaticTypes.itervalues/iteritems gives (ordered) values
    klas.StaticTypes.itervalues/iteritems gives (ordered) types
    *.StaticTypes.itertypes gives (ordered) types
   struct.StaticTypes is readonly - cannot be assigned to, and cannot be setitem'ed
"""

from static_type.util.attr import getattr_local_class_only, getattr_local_instance_only
from static_type.util.str import notSetYet

Container = dict

class Proxy4Container( object):
    """ all this to have instance.StaticType.itervalues() get instance' values.
        also, whatever.StaticType cannot be assigned.
        beware, normaldict.update( Proxy4Container_object) will
        go the generic way through keys() and getitem().
        parent access is readonly, add explicit __setitem__ to allow it.
    """
    __slots__ = [ 'parent', '_getvalue' ]
    #_getattr = staticmethod( getattr_local_instance_only)      #usable only for dict-based obj/_props
    _getattr = getattr                                          #usable for non-dict -based obj/_props
    #XXX see getattr_local_instance_only() - getattr() looks up base-classes!
    def __init__( me, parent, obj, klas =None, notSetYet =notSetYet):
        me.parent = parent
        #me.obj = obj or klas
        #me.is_klas = not obj
        if obj is not None:
            _getattr = me._getattr
            me._getvalue = lambda k: _getattr( obj, k, notSetYet)
        else:
            me._getvalue = parent.__getitem__

    def iteritems( me, order =None):
        'when invoked by class.StaticType, same as itertypes; else yield instance.attr-values'
        _getvalue = me._getvalue
        for k in me.iterkeys( order):
            yield k, _getvalue( k)
    def itervalues( me, order =None):
        _getvalue = me._getvalue
        for k in me.iterkeys( order):
            yield _getvalue( k)

    def itertypes( me, order =None):
        parent = me.parent
        for k in me.iterkeys( order):
            yield k, parent[k]
    def items( me, **kargs):
        return list( me.iteritems(**kargs) )
    def values( me, **kargs):
        return list( me.itervalues(**kargs) )

    #explicit these
    def iterkeys( me, order =None):
        return me.parent.iterkeys( order)
    __iter__ = iterkeys
    def __getitem__( me, key):
        return me.parent[ key]
    def __contains__( me, key):
        return key in me.parent
    def __len__( me):
        return len( me.parent)
    #def __nonzero__( me):
    #    return bool( me.parent)

    #add this to allow writing to the dict
    #def __setitem__ ...

    #override to avoid the generic way via keys()/getitem()
    def update( me, other):
        if isinstance( other, Proxy4Container):
            other = other.parent
        return me.parent.update( other)

    #all else goes parent
    def __getattr__( me, name):
        return getattr( me.parent, name)


class Proxy4Container_order( Proxy4Container):
    __slots__ = [ '_getorder', ]
    order_name = '_order_flat'
    _getmeta_attr_inst = staticmethod( getattr_local_class_only )  #getattr_local_instance_and_class
    _getmeta_attr_klas = staticmethod( getattr_local_instance_only )
    def __init__( me, parent, obj, klas =None, *a,**k):
        Proxy4Container.__init__( me, parent, obj, klas, *a,**k )
        order_name = me.order_name
        if obj is not None:
            _getmeta_attr = me._getmeta_attr_inst
            me._getorder = lambda : _getmeta_attr( obj, order_name, None)
        else:
            _getmeta_attr = me._getmeta_attr_klas
            me._getorder = lambda : _getmeta_attr( klas, order_name, None)

    def iterkeys( me, order =None):
        if order is None:
            order = me._getorder()
        return me.parent.iterkeys( order)

class Descriptor4Container( Container ):
    def __init__( me, Proxy4Container, notSetYet =notSetYet):
        me.Proxy4Container = Proxy4Container
        me.notSetYet = notSetYet
        Container.__init__( me)
    _klasProxy = None
    def __get__( me, obj, klas, **kargs_ignore):
        if obj is None:
            r = me._klasProxy
            if r is None:
                r = me._klasProxy = me.Proxy4Container( me, obj, klas, me.notSetYet)
            return r
        return me.Proxy4Container( me, obj, klas, me.notSetYet)
    def iterkeys( me, order =None):
        if order is not None:
            for k in order:
                if k in me:
                    yield k
        else:
            for k in dict.iterkeys( me):
                yield k

if __name__=='__main__':
    from static_type.util.str import make_str
    class Q( object):
        _myorder = ['a','b','c']
        class Proxy4Container2( Proxy4Container_order):
            order_name = '_myorder'
        types = Descriptor4Container( Proxy4Container2)
        a = types.setdefault( 'a', int)
        b = types.setdefault( 'b', long)
        c = types.setdefault( 'c', float)
        def __init__( me):
            me.a = 1
            me.b = 2
            #me.c = 3
        def __str__( me):
            return make_str( me, me.types.iterkeys(), getattr= getattr_local_instance_only)

    q = Q()
    print 'inst.iteritems', list( q.types.iteritems())
    print 'klas.iteritems', list( Q.types.iteritems())
    print 'inst.itertypes', list( q.types.itertypes())
    print 'inst:', q
    print 'klas:', make_str( Q, Q.types.iterkeys(), name_name='__name__')

    print 'indexing:', q.types, '["a"] =', q.types['a']

    keys = q.types.keys
    print 'keys - from parent', keys, keys()

    try:
        q.types['a'] = 1
    except TypeError: pass
    else: assert not 'types must not allow item assignment'


# vim:ts=4:sw=4:expandtab
