#$Id$
# -*- coding: cp1251 -*-

from atomary import Number

class Number( Number):
    def _int_factory( name, typ, bytes, type_cxx =None, signed =False ):
        _max = ~(~typ(0) << (8*bytes - signed))
        _min = signed and -_max-1 or 0
        def ctor( klas, min=_min, max=_max, type_description=name, type_cxx=type_cxx, **kargs):
            assert _min <= min <= max <= _max
            return klas( typ, min=min, max=max, type_description=type_description, type_cxx=type_cxx, **kargs)
        return classmethod( ctor)

    CHAR  = _int_factory( 'CHAR',   int,  1, 'char'           ,signed=True )
    UCHAR = _int_factory( 'UCHAR',  int,  1, 'unsigned char'  )
    SHORT = _int_factory( 'SHORT',  int,  2, 'short'          ,signed=True )
    USHORT= _int_factory( 'USHORT', int,  2, 'unsigned short' )
    LONG  = _int_factory( 'LONG',   int,  4, 'long'           ,signed=True )
    ULONG = _int_factory( 'ULONG',  long, 4, 'unsigned long'  )
    #BOOL  = _int_factory( 'BOOL',   bool, 1)
    @classmethod
    def FLOAT( klas, *a,**k):
        return klas( type=float, type_description= 'FLOAT', type_cxx= 'float', *a,**k)
    @classmethod
    def DOUBLE( klas, *a,**k):
        return klas( type=float, type_description= 'DOUBLE', type_cxx= 'double', *a,**k)
#    class DOUBLE( Number):
#        def __init__( me, *a,**k):
#            Number.__init__( type=float, type_description= 'DOUBLE', type_cxx= 'double', *a,**k)

# vim:ts=4:sw=4:expandtab
