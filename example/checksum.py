#$Id$

import itertools

class Tchecksum_validator:
    """
    arguments:
        checksumer - functor( iter_over_attributes) producing checksum
        data_converter - converter from attr to checksumer-input;
                            default is None; use  str  for util.checksum funcs
        autocalc_trigger - validating with value of autocalc_trigger
                            will recalc; default is None
        flat_name - name of attribute giving the (ordered) list to attributes to walk through
    if value validated is not the autocalc_trigger,
        get raises MissingAttribute if something in the list is not set
        set raises InvalidChecksum if value not matching calculated value
    """
    MissingAttribute = AttributeError
    InvalidChecksum  = ValueError
    def __init__( me, checksumer,
                        data_converter =None,   #str for util.checksum
                        autocalc_trigger =None,
                        flat_name ='_order_flat' ):
        me.flat_name = flat_name
        me.checksumer = checksumer
        me.data_converter = data_converter
        me.autocalc_trigger = autocalc_trigger
    def validator( me, value, instance, name):
        order = getattr( instance, me.flat_name)
        data_converter = me.data_converter
        if data_converter:
            def getdata(a): return data_converter( getattr( instance,a))
        else:
            def getdata(a): return getattr( instance,a)
        iorder = itertools.imap( getdata, itertools.ifilter( lambda n: n != name, order))
        checksumer = me.checksumer
        try:
            chk = checksumer( iorder)
        except AttributeError, e:
            raise me.MissingAttribute, e.args

        if value == me.autocalc_trigger:
            value = chk
        else:
            if value != chk:
                raise me.InvalidChecksum, 'set wrong checksum %r with %r' % (chk, value)
        return value
    __call__ = validator

from static_type.engine import StaticType

######## example over any StaticType

def Tchecksum1( *a,**k):
    return StaticType( None, validator=Tchecksum_validator( *a,**k))

######## example for StaticType3 - via descriptor

class Tchecksum2( StaticType, Tchecksum_validator):
    """ example:
            from checksum import checksumer_crc32
            chk = Tchecksum( checksumer_crc32( in_iter=True, out_hex=True) )
    """
    class AutocalcTrigger: pass
    class InvalidChecksum( Exception): pass
    class MissingAttribute( Exception): pass
    def __init__( me, checksumer, data_converter =str, autocalc_trigger =AutocalcTrigger, flat_name ='_order_flat' ):
        Tchecksum_validator.__init__( me, checksumer, data_converter=data_converter, autocalc_trigger=autocalc_trigger, flat_name=flat_name)
        StaticType.__init__( me)

    def _validate( me, value, instance):
        return Tchecksum_validator.validator( me, value, instance, me.name)
    def _make_validate( me ): pass  #overload as all typecheck is in _validate

# vim:ts=4:sw=4:expandtab
