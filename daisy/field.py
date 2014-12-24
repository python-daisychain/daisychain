import inspect
import copy


class Field(object):

    def __init__(self, instance_of=None, optional=False, validator=None, default=None):
        self.instance_of = instance_of
        if default is not None:
            optional = True
        self.optional = optional
        self.validator = validator
        self.default = default

    def check_value(self, source, attribute_name, value):
        if self.optional and value == self.default:
            return

        if self.instance_of is not None and not isinstance(value, self.instance_of):
            raise TypeError("{source!r} expects an instantiation argument {attribute_name} which should be an instance of {field.instance_of!r} but was {value.__class__!r}".format(field=self, source=source, attribute_name=attribute_name, value=value))

        if self.validator is not None:
            try:
                result = self._get_validator(source, attribute_name, self.validator)(value)
                if result is not None:
                    assert result, "Result from validating {!r} is not None or evaluates true but {!r}".format(value, result)
            except Exception as e:
                raise TypeError("{source!r} tried to validate the attribute {attribute_name!r} with the value {value!r} and got an exception {exception!s}".format(source=source, attribute_name=attribute_name, value=value, exception=e))

    def _get_validator(self, source, attribute_name, validator):
        if isinstance(validator, basestring):
            if not hasattr(source, validator):
                raise TypeError("{source!r} has an attribute {attribute_name!r} specified by name as {validator!r} that doesn't exist as a class method on the object".format(source=source, attribute_name=attribute_name, validator=validator))
            validator = getattr(source, validator)

        if inspect.ismethoddescriptor(validator) or inspect.ismethod(validator):
            # Necessary for class methods inside class definitions as validations
            validator = validator.__get__(source, type(source))

        if not callable(validator):
            raise TypeError("{source!r} has an attribute {attribute_name!r} that specifies a validator that is not callable".format(source=source, attribute_name=attribute_name))

        # Necessary to use instance_methods inside class definitions as validations
        if inspect.isfunction(validator):
            argspec = inspect.getargspec(validator)
            if len(argspec.args) >= 2 and 'self' == argspec.args[0]:
                def wrapper(value):
                    return validator(source, value)
                return wrapper

        return validator


class ListField(Field):
    def __init__(self, elements_of=None, optional=False, validator=None, element_validator=None, default=None):
        super(ListField, self).__init__(instance_of=list, optional=optional, validator=validator, default=default)
        if self.optional and self.default is None:
            self.default = list()
        self.elements_of = elements_of
        self.element_validator = element_validator

    def check_value(self, source, attribute_name, value):
        super(ListField, self).check_value(source=source, attribute_name=attribute_name, value=value)
        for element in value:
            if self.elements_of is not None and not isinstance(element, self.elements_of):
                raise TypeError("{source!r} expects an instantiation argument {attribute_name} which should have elements of {field.elements_of!r} but found {value.__class__!r}".format(field=self, source=source, attribute_name=attribute_name, value=element))

            if self.element_validator is not None:
                try:
                    result = self._get_validator(source, attribute_name, self.element_validator)(element)
                    if result is not None:
                        assert result, "Result from element_validator for {!r} is not None or True but {!r}".format(element, result)
                except Exception as e:
                    raise TypeError("{source!r} tried to validate the element of the attribute {attribute_name!r} with a value of {value!r} and got an exception {exception!s}".format(source=source, attribute_name=attribute_name, value=value, exception=e))


class ValidatingObject(object):

    def __init__(self, **fields):
        super(ValidatingObject, self).__init__()
        self.__fields__ = dict()
        for field_attr, field in self.__class__._find_fields():
            if field_attr not in fields:
                if not field.optional:
                    raise TypeError("{0!r} requires the keyword-argument {1!r}".format(self.__class__, field_attr))
                else:
                    fields[field_attr] = copy.deepcopy(field.default)
            field_value = fields.pop(field_attr)
            field.check_value(source=self, attribute_name=field_attr, value=field_value)

            setattr(self, field_attr, field_value)
            self.__fields__[field_attr] = field

        if len(fields) > 0:
            raise TypeError("__init__() got an unexpected keyword arguments: {!r}".format(fields.keys()))

    @classmethod
    def _find_fields(cls):
        return ((attr_name,  getattr(cls, attr_name)) for attr_name in dir(cls) if isinstance(getattr(cls, attr_name), Field))

    @classmethod
    def _split_fields(cls, **kwargs):
        """
        Splits off field entries from the other kwargs returning a tuple of dictionaries (fields, non_fields).  Useful for forwarding
        parameters as part of a different library call
        """
        fields = dict()
        non_fields = kwargs
        for attr_name, field in cls._find_fields():
            if attr_name in non_fields:
                fields[attr_name] = non_fields.pop(attr_name)
        return (fields, non_fields)
