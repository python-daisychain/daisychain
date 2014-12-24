from daisy.field import Field, ListField, ValidatingObject
from py3compat import string_types

def outside_function_validator(value):
    assert value, "Outside validation failed"

class TestValid(ValidatingObject):
    CLASS_CONSTANT = 3
    @classmethod
    def class_method_validator(cls, value):
        assert cls.CLASS_CONSTANT - 1 <= value <= cls.CLASS_CONSTANT + 1

    def __init__(self, **fields):
        self.instance_variable = 'pass'
        super(TestValid, self).__init__(**fields)

    def instance_method_validator(self, value):
        assert value.startswith(self.instance_variable)

    validate_by_outside_function = Field(instance_of=(bool, ) + string_types, default=True, optional=True, validator=outside_function_validator)
    validate_by_class_method = Field(instance_of=int, default=3, optional=True, validator=class_method_validator)
    validate_by_instance_method = Field(instance_of=string_types, default='passes', optional=True, validator=instance_method_validator)

def test_outside_function_validation_bool():
    ob = TestValid(validate_by_outside_function=True)
    assert ob.validate_by_outside_function is True, "Did not set outside function"

def test_outside_function_validation_basestring():
    ob = TestValid(validate_by_outside_function='also true')
    assert ob.validate_by_outside_function == 'also true', "Did not set outside function"

def test_outside_function_validation_bad_type():
    try:
        ob = TestValid(validate_by_outside_function=None)
    except TypeError:
        pass
    else:
        assert False, "Checking outside function validation did not work for raising an error using 'None'"

def test_outside_function_not_valid():
    try:
        ob = TestValid(validate_by_outside_function=False)
    except TypeError:
        pass
    else:
        assert False, "Checking outside function validation did not work for raising an error using 'False'"

    try:
        ob = TestValid(validate_by_outside_function='')
    except TypeError:
        pass
    else:
        assert False, "Checking outside function validation did not work for raising an error using an empty string"

def test_outside_function_setting_not_optional():
    TestValid.validate_by_outside_function.optional = False
    try:
        ob = TestValid()
    except TypeError:
        pass
    else:
        assert False, "Checking outside function validation did not work for raising an error when not optional"
    finally:
        TestValid.validate_by_outside_function.optional = True

def test_validate_by_class_method_valid():
    ob = TestValid()
    assert ob.validate_by_class_method == 3, "Default not working through validate_by_class_method"

    ob = TestValid(validate_by_class_method=2)
    assert ob.validate_by_class_method == 2, "Value not passed through validate_by_class_method"

def test_validate_by_class_method_invalid():
    try:
        ob = TestValid(validate_by_class_method=1)
    except TypeError:
        pass
    else:
        assert False, "Checking class method when passing an invalid value of 1 did not raise an error"


def test_validate_by_class_method_bad_type():
    try:
        ob = TestValid(validate_by_class_method='3')
    except TypeError:
        pass
    else:
        assert False, "Checking class method when passing an invalid value of '3' did not raise an error"

def test_validate_by_instance_method_valid():
    ob = TestValid()
    assert ob.validate_by_instance_method == 'passes', "Default not working through validate_by_class_method"
    ob = TestValid(validate_by_instance_method='pass')
    assert ob.validate_by_instance_method == 'pass', "Value not passed through instance variable"
    ob = TestValid(validate_by_instance_method='passable')
    assert ob.validate_by_instance_method == 'passable', "Value not passed through instance variable"

def test_validate_by_instance_method_invalid():
    try:
        ob = TestValid(validate_by_instance_method='fail')
    except TypeError:
        pass
    else:
        assert False, "Validating by instance method when passing an invalid value of 'fail' did not raise an error"

    try:
        ob = TestValid(validate_by_instance_method='not_pass')
    except TypeError:
        pass
    else:
        assert False, "Validating by instance method when passing an invalid value of 'fail' did not raise an error"

def test_instance_method_after_class_creation():
    try:
        TestValid.after_creation = Field(validator=TestValid.instance_method_validator)
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was given a type that would cause the validation to raise an exception"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was given a type that would cause the validation to assert incorrectly"

        ob = TestValid(after_creation='passes')
        assert ob.after_creation == 'passes', "Value not passed through instance variable"
        ob = TestValid(after_creation='pass')
        assert ob.after_creation == 'pass', "Value not passed through instance variable"
        ob = TestValid(after_creation='passable')
        assert ob.after_creation == 'passable', "Value not passed through instance variable"

    finally:
        delattr(TestValid, 'after_creation')

def test_class_method_after_class_creation():
    try:
        TestValid.after_creation = Field(validator=TestValid.class_method_validator)
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was given a type that would cause the validation to raise an exception"

        try:
            ob = TestValid(after_creation=10000)
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was given a type that would cause the validation to assert incorrectly"

        ob = TestValid(after_creation=3)
        assert ob.after_creation == 3, "Value not passed through instance variable"
        ob = TestValid(after_creation=2)
        assert ob.after_creation == 2, "Value not passed through instance variable"
        ob = TestValid(after_creation=4)
        assert ob.after_creation == 4, "Value not passed through instance variable"

    finally:
        delattr(TestValid, 'after_creation')


def test_by_adhoc_lambda_after_class_creation():
    try:
        TestValid.validate_by_adhoc_lambda = Field(validator=lambda x: 0 <= x <= 1000)
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating by adhoc lambda after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(validate_by_adhoc_lambda='kadslfja')
        except TypeError:
            pass
        else:
            assert False, "validating by adhoc lambda after class creation failed to raise an error when passed a value that would cause the validation to raise an error"

        try:
            ob = TestValid(validate_by_adhoc_lambda=1000000)
        except TypeError:
            pass
        else:
            assert False, "validating by adhoc lambda after class creation failed to raise an error when passed a value that would cause the validation to return False"

        ob = TestValid(validate_by_adhoc_lambda=0)
        assert ob.validate_by_adhoc_lambda == 0, "Value not passed through instance variable"
        ob = TestValid(validate_by_adhoc_lambda=10)
        assert ob.validate_by_adhoc_lambda == 10, "Value not passed through instance variable"
        ob = TestValid(validate_by_adhoc_lambda=1000)
        assert ob.validate_by_adhoc_lambda == 1000, "Value not passed through instance variable"
        ob = TestValid(validate_by_adhoc_lambda=50.12)
        assert ob.validate_by_adhoc_lambda == 50.12, "Value not passed through instance variable"
    finally:
        delattr(TestValid, 'validate_by_adhoc_lambda')



def test_list_field_by_adhoc_lambda_after_class_creation():
    try:
        TestValid.validate_by_adhoc_lambda = ListField(validator=lambda x: len(x) >= 3, elements_of=(int, float), element_validator=lambda y: 0 <= y <= 1000)
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(validate_by_adhoc_lambda=[0, 1])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause the list validation to raise an error"

        try:
            ob = TestValid(validate_by_adhoc_lambda=[0, '12', 2])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause one element of the validation to raise an error for bad type"

        try:
            ob = TestValid(validate_by_adhoc_lambda=['0', '12', '2'])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause all elements to raise an error for bad types"

        try:
            ob = TestValid(validate_by_adhoc_lambda=[1300, 0, 2])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause one element of the validation to raise an error for invalid value"

        try:
            ob = TestValid(validate_by_adhoc_lambda=[1300, -30, 4000])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause all elements to raise an error for invalid values"

        try:
            ob = TestValid(validate_by_adhoc_lambda=[1300, '-30', 4000])
        except TypeError:
            pass
        else:
            assert False, "validating list field by adhoc lambda after class creation failed to raise an error when passed a value that would cause all elements to raise an error for mix of invalid types and invalid values"

        ob = TestValid(validate_by_adhoc_lambda=[0, 0, 0])
        assert ob.validate_by_adhoc_lambda == [0, 0, 0], "Value not passed through instance variable"
        ob = TestValid(validate_by_adhoc_lambda=[0, 1000, 5])
        assert ob.validate_by_adhoc_lambda == [0, 1000, 5], "Value not passed through instance variable"
        ob = TestValid(validate_by_adhoc_lambda=[12.2, 400, 12.5, 60.2])
        assert ob.validate_by_adhoc_lambda == [12.2, 400, 12.5, 60.2], "Value not passed through instance variable"
        TestValid.validate_by_adhoc_lambda = ListField(validator=lambda x: len(x) >= 3, elements_of=(int, float), element_validator=lambda y: 0 <= y <= 1000, optional=True)
        ob = TestValid()
        assert ob.validate_by_adhoc_lambda == [], "Default list value not getting passed through properly"

    finally:
        delattr(TestValid, 'validate_by_adhoc_lambda')

def test_validator_using_attribute_name_for_instance_validator():
    try:
        TestValid.after_creation = Field(validator='instance_method_validator')
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was given a type that would cause the validation to raise an exception"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using instance method after class creation failed to raise an error when it was given a type that would cause the validation to assert incorrectly"

        ob = TestValid(after_creation='passes')
        assert ob.after_creation == 'passes', "Value not passed through instance variable"
        ob = TestValid(after_creation='pass')
        assert ob.after_creation == 'pass', "Value not passed through instance variable"
        ob = TestValid(after_creation='passable')
        assert ob.after_creation == 'passable', "Value not passed through instance variable"

    finally:
        delattr(TestValid, 'after_creation')

def test_validator_using_attribute_name_for_class_method():
    try:
        TestValid.after_creation = Field(validator='class_method_validator')
        try:
            ob = TestValid()
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was a required field"

        try:
            ob = TestValid(after_creation='fail')
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was given a type that would cause the validation to raise an exception"

        try:
            ob = TestValid(after_creation=10000)
        except TypeError:
            pass
        else:
            assert False, "validating by using class method after class creation failed to raise an error when it was given a type that would cause the validation to assert incorrectly"

        ob = TestValid(after_creation=3)
        assert ob.after_creation == 3, "Value not passed through instance variable"
        ob = TestValid(after_creation=2)
        assert ob.after_creation == 2, "Value not passed through instance variable"
        ob = TestValid(after_creation=4)
        assert ob.after_creation == 4, "Value not passed through instance variable"

    finally:
        delattr(TestValid, 'after_creation')


def test_validator_using_bad_attribute_name():
    try:
        TestValid.after_creation = Field(validator='no_validation_method_by_this_name')
        try:
            ob = TestValid(after_creation=10)
        except TypeError:
            pass
        else:
            assert False, "Validation using an invalid validation attribute name did not throw an error and should have"

    finally:
        delattr(TestValid, 'after_creation')

def test_validator_using_non_callable_validator():
    try:
        TestValid.after_creation = Field(validator=10)
        try:
            ob = TestValid(after_creation=10)
        except TypeError:
            pass
        else:
            assert False, "Validation using an invalid validator that is not callable did not throw an error and should have"

    finally:
        delattr(TestValid, 'after_creation')



def test_validator_using_an_attribute_name_that_is_not_callable():
    try:
        TestValid.after_creation = Field(validator='instance_variable')
        try:
            ob = TestValid(after_creation=10)
        except TypeError:
            pass
        else:
            assert False, "Validation using a non-callable validator specified by attribute name did not throw an error and should have"

    finally:
        delattr(TestValid, 'after_creation')


def test_validating_object_when_thrown_unknown_kwargs():
    try:
        ob = TestValid(unknown_kwarg=None)
    except TypeError:
        pass
    else:
        assert False, "Validating object should have thrown a type-error on kwargs for no known field being passed to it"
