from daisy.steps.compiler import Compiler
from daisy.constants import CLASS_KEY
from daisy.importer import find_class


class NamespaceCompiler(Compiler):
    """
    Compiles sections containing a '__namespaces__' section and uses those namespaces as the path to find valid
    classes.  Allows for shortened formatting of '__class__' attributes
    """
    NAMESPACES_KEY = '__namespaces__'

    def find_subsections_specifying_key(self, key, config, ignore_if_key_present=None):
        self.log('compiler').debug("Searching {!r} for {!r} ignoring {!r}".format(config, key, ignore_if_key_present))
        if isinstance(config, dict):
            if key in config:
                self.log('compiler').debug('Found config: {!r}'.format(config))
                yield config
            elif ignore_if_key_present is not None and ignore_if_key_present in config:
                self.log('compiler').debug('Ignored config: {!r}'.format(config))

            for subsection in self.find_subsections_specifying_key(key, list(config.values()), ignore_if_key_present):
                yield subsection
        elif isinstance(config, (list, tuple)):
            for subsection in config:
                for found_subsection in self.find_subsections_specifying_key(key, subsection, ignore_if_key_present):
                    yield found_subsection

    def compile(self, config):
        for namespace_section in self.find_subsections_specifying_key(self.NAMESPACES_KEY, config):
            namespaces = namespace_section.pop(self.NAMESPACES_KEY)
            for class_section in self.find_subsections_specifying_key(CLASS_KEY, namespace_section, self.NAMESPACES_KEY):
                if self.NAMESPACES_KEY in class_section:
                    class_namespaces = class_section.pop(self.NAMESPACES_KEY)
                else:
                    class_namespaces = namespaces
                self.log('compiler').debug('Attempting to find a class for {!r} based on namespaces:{!r}'.format(class_section, class_namespaces))
                module_name, cls = find_class(class_section[CLASS_KEY], class_namespaces)
                if module_name is None:
                    self.log('compiler').error('Could not find a class for {!r} based on the namespaces:{!r}'.format(class_section, class_namespaces))
                else:
                    class_section[CLASS_KEY] = cls.__module__ + '.' + cls.__name__
        return config
