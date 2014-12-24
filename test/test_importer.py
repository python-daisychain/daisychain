from daisychain.importer import find_class, module_cache, find_class_based_on_path
from daisychain.log import SharedLoggingObject
from daisychain.steps.inputs.file import InputFile

def test_find_class_no_namespaces():
    module_name, cls = find_class('daisychain.log.SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_with_full_path_when_namespaces_specified():
    module_name, cls = find_class('daisychain.log.SharedLoggingObject', namespaces=['daisychain'])
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_with_partial_namespace():
    module_name, cls = find_class('log.SharedLoggingObject', namespaces=['daisychain'])
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_with_full_namespace():
    module_name, cls = find_class('SharedLoggingObject', namespaces=['daisychain.log'])
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_with_full_namespace_where_namespace_is_not_first():
    module_name, cls = find_class('SharedLoggingObject', namespaces=['', 'daisychain.steps', 'daisychain.log'])
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_with_full_namespace_where_namespace_is_not_last():
    module_name, cls = find_class('SharedLoggingObject', namespaces=['daisychain.log', 'daisychain.steps'])
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_cannot_find_class():
    module_name, cls = find_class('SharedLoggingObject', namespaces=['daisychain.steps'])
    assert module_name is None
    assert cls is None
    module_cache.clear()


def test_find_class_based_on_path_no_wildcards():
    module_name, cls = find_class_based_on_path('daisychain.log','SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()


def test_find_class_based_on_path_with_wildcards():
    module_name, cls = find_class_based_on_path('daisychain.*','SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.log*','SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.l*g','SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()


    module_name, cls = find_class_based_on_path('daisychain.**','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.steps.**','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.steps.inputs.**','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.steps.**.file','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.**.file','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.ste**.file','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.steps.inputs.file**','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.**.inputs.**','InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.**.*.*', 'InputFile')
    assert module_name == 'daisychain.steps.inputs.file'
    assert cls is InputFile
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.log.*','SharedLoggingObject')
    assert module_name == 'daisychain.log'
    assert cls is SharedLoggingObject
    module_cache.clear()

def test_find_class_based_on_path_invalid():
    module_name, cls = find_class_based_on_path('daisychain.*.*.*.file', 'InputFile')
    assert module_name is None
    assert cls is None
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.*.log','SharedLoggingObject')
    assert module_name is None
    assert cls is None
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.log', 'NoClassToFind')
    assert module_name is None
    assert cls is None
    module_cache.clear()

    module_name, cls = find_class_based_on_path('daisychain.log', 'logging')
    assert module_name is None
    assert cls is None
    module_cache.clear()

    try:
        module_name, cls = find_class_based_on_path('daisychain.***.log','SharedLoggingObject')
    except ImportError:
        pass
    else:
        assert False, "Should raise an error if '***' is in the path (uninterpretable wildcard)"
    finally:
        module_cache.clear()

    try:
        module_name, cls = find_class_based_on_path('*.log','SharedLoggingObject')
    except ImportError:
        pass
    else:
        assert False, "Should raise an error if trying to search under the global path"
    finally:
        module_cache.clear()


