#$Id$
# -*- coding: cp1251 -*-

from base import StaticStruct, SubStruct, config

class ForwardSubStruct( StaticStruct):
    auto_set = None     #else SubStruct.default kicks in too early
    def __new__( klas, whoo, **kargs):
        class _Forwarder( ForwardSubStruct):
            who = whoo
        return SubStruct( _Forwarder, **kargs)

    @staticmethod
    def resolve( namespace, base_klas =StaticStruct, debug =False):
        return _resolver.resolve( namespace, base_klas=base_klas, debug=debug)
    @staticmethod
    def resolve1( typ, namespace, base_klas =StaticStruct, debug =False):
        return _resolver.resolve1( typ, debug=debug, *namespaces)

from static_type.util.forward_resolver import Resolver
class Resolver( Resolver):
    dbgpfx = 'ForwardSubStruct.'
    def is_forward_decl( me, typ):
        return issubclass( typ.typ, ForwardSubStruct) and typ.typ.who
    def klas_reftype_iterator( me, klas):
        for k,typ in klas.StaticType.itertypes():
            if isinstance( typ, SubStruct):
                yield typ
    exclude = [ ForwardSubStruct ]
    def finisher( me, typ, resolved_klas):
        who = resolved_klas
        assert issubclass( who, StaticStruct)
        #redo the auto_set/default_value stuff
        auto_set = typ.auto_set
        if auto_set is None: auto_set = getattr( who, 'auto_set', SubStruct.auto_set)
        default_value = config.notSetYet
        if auto_set: default_value = who
        if typ.factory is typ.typ: typ.factory = who
        typ.typ = who
        typ.auto_set = auto_set
        typ.default_value = default_value
        typ.forward = True
_resolver = Resolver()

if __name__=='__main__':
    class A( StaticStruct):
        next = ForwardSubStruct('A')
        prev = ForwardSubStruct('A')

    class B( StaticStruct):
        c = ForwardSubStruct( 'C')#, auto_set=1 )
    class C( StaticStruct):
        b = ForwardSubStruct( 'B')#, auto_set=0 )

    ForwardSubStruct.resolve( locals(), debug=1 )

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

    #TODO: test auto_set: setup in combinations of struct/ref

# vim:ts=4:sw=4:expandtab
