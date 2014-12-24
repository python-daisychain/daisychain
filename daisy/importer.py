import importlib
import re
import pkgutil

module_cache = {}
NOT_2_STARS = re.compile(r'(?<!\*)(\*)(?!\*)')


def _get_cached_module(module_name):
    if module_name not in module_cache:
        try:
            module_cache[module_name] = importlib.import_module(module_name)
        except ImportError:
            module_cache[module_name] = None
    return module_cache[module_name]


def _get_class_from_module(mod, class_name):
    if mod is not None and class_name in mod.__dict__ and isinstance(mod.__dict__[class_name], type):
        cls = mod.__dict__[class_name]
        return cls.__module__, cls
    else:
        return None, None


def find_class(rel_class_path, namespaces=None):
    if namespaces is None:
        namespaces = list()

    if '' not in namespaces:
        namespaces.append('')

    rel_class_path = rel_class_path.lstrip('.')
    for namespace in namespaces:
        full_name = '.'.join([namespace.rstrip('.'), rel_class_path]).strip('.')
        if '.' not in full_name:
            continue
        module_name, class_name = full_name.rsplit('.', 1)
        found_module_name, found_class = find_class_based_on_path(module_name, class_name)
        if found_module_name is not None:
            return found_module_name, found_class

    return None, None


def get_smallest_specified_module_name(module_name):
    pieces = []
    for piece in module_name.split('.'):
        if '*' in piece:
            if len(pieces) == 0:
                raise ImportError("Cannot search under all packages because of high performance implications")
            return '.'.join(pieces)
        pieces.append(piece)
    return '.'.join(pieces)


def find_class_based_on_path(path, class_name):
    if '***' in path:
        raise ImportError("Cannot interpret a path that contains more than 3 wildcards in a row")

    base_module_name = get_smallest_specified_module_name(path)
    base_mod = _get_cached_module(base_module_name)
    if base_mod is None:
        return None, None

    if base_module_name == path:
        # Simple case with no wildcards
        return _get_class_from_module(base_mod, class_name)

    if not hasattr(base_mod, '__path__'):
        # base_module doesn't specify a package but a module
        return _get_class_from_module(base_mod, class_name)

    matching_pattern = re.compile(NOT_2_STARS.sub('[\w_]*', path).replace('.', '\.').replace('**', '.*'))
    for importer, module_name, is_package in pkgutil.walk_packages(base_mod.__path__, base_module_name + '.'):
        if matching_pattern.match(module_name):
            cls_module_name, cls = _get_class_from_module(_get_cached_module(module_name), class_name)
            if cls_module_name is not None and cls is not None:
                return cls_module_name, cls
    return None, None
