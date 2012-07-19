#$Id$
#s.dobrev 2k4

from static_type.example.checksum import Tchecksum1 as Tchecksum
from static_type.example.checksum import Tchecksum2 as Tchecksum

def _make_Checksum( itr, hasher =None):
    if not hasher:
        import md5 as hasher
        #import sha as hasher
    s = hasher.new()
    for a in itr:
        s.update( str( a) )
    return s.hexdigest()


########### example structure
from static_type import StaticTyper, StaticType

class Record( StaticTyper) :
    def _validator_ID( v, **k_ignore):
        """ range check """
        if v<=0: raise ValueError, 'value must be positive int, not %r' % v
        return v
    def _validator_Date( v, **k_ignore):
        """ type check and auto_convert """
        if isinstance( v, tuple) and len(v)==2:
            v = '.'.join([ str(x) for x in v] )
        elif not isinstance( v, str):
            raise TypeError, 'expect str or tuple( str,str), not %r of type %s' % (v,type(v))
        return v

    ID   = StaticType( int, auto_convert=True, validator=_validator_ID )
    Date = StaticType( None, validator= _validator_Date)
    Count= StaticType( int)
    Key  = StaticType( str, default_value= 'empty/key/used')
    __slots__ = ()

import time
class Input_Head( StaticTyper):
    #timestamp = StaticType( str, default_value= lambda **k: time.ctime() )
    timestamp = StaticType( str, default_value= lambda **k: 'Fri Jan  5 20:02:20 2002')     #for testout-diff
    __slots__ = ()

class Input_Record( Input_Head, Record):
    Checksum  = Tchecksum( checksumer= _make_Checksum, data_converter= None)
    __slots__ = ()

if 10:      #auto-calc order
    try: __order
    except NameError:
        from svd_util.assignment_order import ASTVisitor4assign
        ASTVisitor4assign().parseFile_of_module( __file__).set_order_in_namespace( globals(), flatten=True, ignore_missing_order=True)

if __name__ == '__main__':
    from svd_util.assignment_order import test, get_class_attributes_flatten_ordered
    import __main__
    test( __main__)

    r = Input_Record()
    r.ID = '357'
    r.Date = (10,'03')
    r.Count = 2
    print r._order_flat
    print r

    try:
        r.Checksum = '1243213'
    except Tchecksum.InvalidChecksum, e: print ' OK Exception', e  #Checksum wrong

    try:
        print r.Checksum
    except AttributeError, e: print ' OK Exception', e  #Checksum not set yet

    try:
        for a,v in get_class_attributes_flatten_ordered( r.__class__, r):
            print a,'\t',v
    except AttributeError, e: print ' OK Exception', e  #Checksum not set yet

    try:
        r.boza = 4
    except AttributeError, e: print ' OK Exception', e  #can not set extra attributes

    r.ID = '5'
    try:
        r.ID = 'rewre'
    except ValueError, e: print ' OK Exception', e      #invalid int literal

# vim:ts=4:sw=4:expandtab
