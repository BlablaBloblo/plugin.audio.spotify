class NonDataProperty:
    """Much like the property builtin, but only implements __get__,
    making it a non-data property, and can be subsequently reset.

    See http://users.rcn.com/python/download/Descriptor.htm for more
    information.

    >>> class X(object):
    ...   @NonDataProperty
    ...   def foo(self):
    ...     return 3
    >>> x = X()
    >>> x.foo
    3
    >>> x.foo = 4
    >>> x.foo
    4
    >>> X.foo
    <jaraco.classes.properties.NonDataProperty object at ...>
    """

    def __init__(self, fget):
        assert fget is not None, "fget cannot be none"
        assert callable(fget), "fget must be callable"
        self.fget = fget

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.fget(obj)


class ClassProperty:
    """
    Like @property but applies at the class level.


    >>> class X(metaclass=ClassProperty.Meta):
    ...   val = None
    ...   @ClassProperty
    ...   def foo(cls):
    ...     return cls.val
    ...   @foo.setter
    ...   def foo(cls, val):
    ...     cls.val = val
    >>> X.foo
    >>> X.foo = 3
    >>> X.foo
    3
    >>> x = X()
    >>> x.foo
    3
    >>> X.foo = 4
    >>> x.foo
    4

    Setting the property on an instance affects the class.

    >>> x.foo = 5
    >>> x.foo
    5
    >>> X.foo
    5
    >>> vars(x)
    {}
    >>> X().foo
    5

    Attempting to set an attribute where no setter was defined
    results in an AttributeError:

    >>> class GetOnly(metaclass=ClassProperty.Meta):
    ...   @ClassProperty
    ...   def foo(cls):
    ...     return 'bar'
    >>> GetOnly.foo = 3
    Traceback (most recent call last):
    ...
    AttributeError: can't set attribute

    It is also possible to wrap a classmethod or staticmethod in
    a classproperty.

    >>> class Static(metaclass=ClassProperty.Meta):
    ...   @ClassProperty
    ...   @classmethod
    ...   def foo(cls):
    ...     return 'foo'
    ...   @ClassProperty
    ...   @staticmethod
    ...   def bar():
    ...     return 'bar'
    >>> Static.foo
    'foo'
    >>> Static.bar
    'bar'

    *Legacy*

    For compatibility, if the metaclass isn't specified, the
    legacy behavior will be invoked.

    >>> class X:
    ...   val = None
    ...   @ClassProperty
    ...   def foo(cls):
    ...     return cls.val
    ...   @foo.setter
    ...   def foo(cls, val):
    ...     cls.val = val
    >>> X.foo
    >>> X.foo = 3
    >>> X.foo
    3
    >>> x = X()
    >>> x.foo
    3
    >>> X.foo = 4
    >>> x.foo
    4

    Note, because the metaclass was not specified, setting
    a value on an instance does not have the intended effect.

    >>> x.foo = 5
    >>> x.foo
    5
    >>> X.foo  # should be 5
    4
    >>> vars(x)  # should be empty
    {'foo': 5}
    >>> X().foo  # should be 5
    4
    """

    class Meta(type):
        def __setattr__(self, key, value):
            obj = self.__dict__.get(key, None)
            if type(obj) is ClassProperty:
                return obj.__set__(self, value)
            return super().__setattr__(key, value)

    def __init__(self, fget, fset=None):
        self.fget = self._fix_function(fget)
        self.fset = fset
        fset and self.setter(fset)

    def __get__(self, instance, owner=None):
        return self.fget.__get__(None, owner)()

    def __set__(self, owner, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        if type(owner) is not ClassProperty.Meta:
            owner = type(owner)
        return self.fset.__get__(None, owner)(value)

    def setter(self, fset):
        self.fset = self._fix_function(fset)
        return self

    @classmethod
    def _fix_function(cls, fn):
        """
        Ensure fn is a classmethod or staticmethod.
        """
        if not isinstance(fn, (classmethod, staticmethod)):
            return classmethod(fn)
        return fn
