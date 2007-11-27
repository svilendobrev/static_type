#$Id$
# s.dobrev 2k4-5
"""
building indexes for StaticType/s
usage:

...all the declarations...
from all import ALL
...#eventualy subclass and specialize

ALL.setup( globals(), __file__, __name__, ..., dict4byname=some_dictOrder)
if __name__ == '__main__':
    ALL.test()
"""

from base import issubclass, Messager, StaticStruct
#from static_type.util.dictOrder import dictOrder

def build_indexes( namespace, base_type,
            ID =True, with_classes =False, check_meta =True, dict4byname =None ):
    index_by_name = dict4byname()
    index_by_id = {}
    r = None
    #parts of this can move into the StaticTyper_factory above
    for name in namespace.get( '_order', namespace):
        try:
            a = namespace[ name ]
        except KeyError:
            continue       #not set yet, e.g. index_by_id
        if isinstance( a, base_type):
            a.name = name
            index_by_name[ name] = a
            if ID:
                index_by_id[ a.ID ] = a
            #may check for duplicate IDs, but NOT for duplicate names

        elif with_classes:
            try:
                if a is base_type: continue
                if not issubclass( a, base_type):
                    if issubclass( a, StaticStruct):
                        a.name = name
                        a.GLOBAL = True
                    continue
            except TypeError: continue

            a.name = name
            index_by_name[ name] = a
            if ID:
                index_by_id[ a.ID ] = a
            #may check for duplicate IDs, but NOT for duplicate names

            if check_meta:
                if r is None: r = base_type()
                aname = a
                for p,v_base in base_type.StaticType.iteritems():
                    if not v_base.meta: continue
                    v = getattr( a, p)
                    if v is v_base:
                        msg_MissingValue( struct=aname, member=p )
                        continue
                    try:
                        s = setattr( r, p, v)
                    except (TypeError,ValueError), e:
                        msg_WrongValue( struct=aname, member=p, value=v, e=e )

    if Messager._errors:
        raise SystemExit, 'checker: %d error(s) found. Stop.' % len( Messager._errors)
    return index_by_name, index_by_id


def build_order( namespace, filename,
        kargs_visitor   ={},
        flatten_later   =False,
        filter_order    =None,
        filter_order_whole =None,
        with_classes    =False,
        **kargs_flatten_order ):
    try: namespace[ '_order' ]
    except KeyError:
        from static_type.util.assignment_order import ASTVisitor4assign
        root = ASTVisitor4assign( **kargs_visitor
                ).parseFile_of_module( filename
                )
#        root.pprint()
#        print '-----------'
        root.set_order_in_namespace( namespace,
                    flatten= not flatten_later,
                    ignore_missing_order= True,
                    with_classes= with_classes,
                    **kargs_flatten_order)
        if flatten_later:
            root.flatten_class__order( namespace,
                                            ignore_missing_order= True,
                                            **kargs_flatten_order)
        if filter_order or filter_order_whole:
            root.filter_order( namespace, attr_filter= filter_order, order_filter= filter_order_whole)

def build_order_indexes( base_type, namespace, filename,
            ID =True, with_classes =False, check_meta =True, dict4byname =None,
            **kargs):
    build_order( namespace, filename, with_classes=with_classes, **kargs)
    return build_indexes( namespace, base_type=base_type, ID=ID,
            with_classes=with_classes, check_meta=check_meta, dict4byname=dict4byname)


class ALL:
    by_name = None
    by_id = None
    @staticmethod       #not class! pass klas in    ?
    def setup( klas, namespace, filename, modname, base, **kargs):
        klas.filename = filename
        klas.modname  = modname
        klas.by_name, klas.by_id = build_order_indexes( base, namespace, filename, **kargs)
        #if modname == '__main__': klas.test()

    @classmethod
    def test( klas):
        print klas.modname, 'items: {'
        for av in klas.by_name.iteritems():
            print '  %s = %s' % av
        print '}'

# vim:ts=4:sw=4:expandtab
