#$Id$
#s.dobrev 2k4

class StaticTyper_factory( type):
    '''metaclass for types/structs containing statictypes.
    inherit, then override the staticmethod convert
    be careful with __slots__; multiple inheritance with bases with different non-empty __slots__
    raise TypeError: mixed instance lay-out; this can be fixed if all __slots__ are combined in one.
    Also, if some base has __dict__, the result will always has it, and it overrides statictypes!
    '''
    def __new__( meta, name, bases, adict):
            #change dynamicaly class name
        name = adict.pop( '__name__DYNAMIC', name)

            #change dynamicaly class bases
        bases = adict.pop( '__bases__DYNAMIC', bases )

            #add dynamic attribute-definitions
        adict.update( adict.pop( '__dict__DYNAMIC', () ) )
        if '_DYNAMIC_' in adict:
            import warnings
            warnings.warn( RuntimeWarning( '"_DYNAMIC_" is deprecated, use __dict__ instead' ) )
            adict.update( adict.pop( '_DYNAMIC_', () ) )

            #inplace conversion
        meta.convert( meta, name, bases, adict)
        return type.__new__( meta, name, bases, adict)

    #@staticmethod
    #def convert( klas, name, bases, adict):
    #    ...
    # not classmethod!! - because ParentClass.convert() must see thigs defined here and up,
    #   which is not possible with classmethods invoked this way - they see their own only


''' make yourBaseType( StaticTyper ) class with a
        class_attribute = typedef for each required instance attribute-name.
    set __slots__ = () to avoid __dict__'s / disallow extra attributes.
'''

class StaticType_ValueContainer: pass

class StaticTyper( object):
    '''the base type/struct containing statictypes.
    inherit, then:
        __metaclass__ = yourStaticTyper_factory
        __slots__ = ()      #do not introduce __dict__ - any base with __dict__ forces it
    '''
    @property
    def _props( me):
        try: p = me._me_props
        except AttributeError:
            p = me._me_props = getattr( me, 'StaticType_ValueContainer', StaticType_ValueContainer)()
        return p
    __slots__ = ( '_me_props', )        #do not introduce __dict__

#or equivalent:
#StaticTyper = StaticTyper_factory( 'StaticTyper', ( object, ), { ... } )

# vim:ts=4:sw=4:expandtab
