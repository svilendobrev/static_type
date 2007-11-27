#$Id$
# -*- coding: cp1251 -*-

from base import StaticStruct, SubStruct, config

class ForwardSubStruct( StaticStruct):
    def __new__( klas, whoo, **kargs):
        class _Forwarder( ForwardSubStruct):
            who = whoo
        return SubStruct( _Forwarder, **kargs)

    @staticmethod
    def resolve( alldict, debug =False):
        from static_type.util.attr import issubclass
        for item in alldict.itervalues():
            if item is ForwardSubStruct: continue
            if not issubclass( item, StaticStruct): continue
            klas = item
            for k,v in klas.StaticType.itertypes():
                if isinstance( v, SubStruct):
                    if issubclass( v.typ, ForwardSubStruct):
                        #print klas, k,v
                        try:
                            who = alldict[ v.typ.who]
                        except KeyError:
                            print klas, k,v, v.typ.who
                            print alldict
                            raise
                        assert issubclass( who, StaticStruct)
                        #redo the auto_set/default_value stuff
                        auto_set = getattr( who, 'auto_set', SubStruct.auto_set)
                        default_value = config.notSetYet
                        if auto_set: default_value = who
                        if v.factory is v.typ: v.factory = who
                        v.typ = who
                        v.auto_set = auto_set
                        v.default_value = default_value
                        v.forward = True
                        if debug: print 'ForwardSubStruct.resolve', klas, v
        return alldict

if __name__=='__main__':
    class A( StaticStruct):
        next = ForwardSubStruct('A')
        prev = ForwardSubStruct('A')

    class B( StaticStruct):
        c = ForwardSubStruct( 'C')#, auto_set=1 )
    class C( StaticStruct):
        b = ForwardSubStruct( 'B')#, auto_set=0 )

    ForwardSubStruct.resolve( locals(), 1 )

    assert A.next.typ is A
    assert A.prev.typ is A
    assert B.c.typ is C
    assert C.b.typ is B

    #test recursive auto_set
    ForwardSubStruct.auto_set = 1
    b = B()
    c = C()
    z = b.c
#    x = c.b
#    print id(z)
#    print id(x)
    print b

# vim:ts=4:sw=4:expandtab
