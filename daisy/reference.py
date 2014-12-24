from collections import defaultdict
from daisy.log import SharedLoggingObject
from daisy.field import Field, ListField, ValidatingObject
from daisy.constants import MAXIMUM_REFERENCE_DEPTH
from py3compat import string_types


class CircularReferenceError(Exception):
    def __init__(self, node):
        super(CircularReferenceError, self).__init__("Circular Reference Found: %r" % node)
        self.root_node = node
        self.num_nodes = 0
        self.circle_closed = False

    def add_reference(self, node, attribute_names):
        if self.circle_closed:
            return False

        if node is self.root_node:
            self.circle_closed = True

        if self.circle_closed and self.num_nodes == 0:
            self.args = (self.args[0] + ' refers to itself through {!s}'.format(', '.join(sorted(attribute_names))),)
        else:
            self.args = ('{!r}.{!s}\n\t-> '.format(node, ', '.join(sorted(attribute_names))) + self.args[0],)
            self.num_nodes = 1

        return True


class ExceedsMaximumDepthError(RuntimeError):
    def __init__(self):
        super(ExceedsMaximumDepthError, self).__init__('Maximum recursion depth ({}) exceeded.  This exists because of the inherent problem of possible segfaults on stack depth.'.format(MAXIMUM_REFERENCE_DEPTH))


class Reference(Field):
    """
    Reference object for identifying attributes for an object that reference another part of the release plan

    param argument: Variable name that has the references and will be overwritten by the referenced objects
    type argument: string_types
    param instance_of: Optional parameter used to type-check that the reference is an instance of this class or, if a tuple, any of those classes
    type instance_of: type or tuple of types
    param multiple: Optional parameter to specify if this reference can be a list of references instead of a single item
    type multiple: bool
    param optional: Specifies if the attribute is not required.  Default: False.  If it is optional, the value of the attribute will be 'None'
    type optional: bool
    """

    def __init__(self, instance_of=None, optional=False, validator=None, default=None, affects_execution_order=True):
        super(Reference, self).__init__(instance_of=instance_of, optional=optional, validator=validator, default=default)
        self.affects_execution_order = affects_execution_order


class ReferenceList(ListField, Reference):
    def __init__(self, elements_of=None, optional=False, validator=None, element_validator=None, affects_execution_order=True):
        super(ReferenceList, self).__init__(elements_of=elements_of, optional=optional, validator=validator, element_validator=element_validator)
        self.affects_execution_order = affects_execution_order


class ReferencingObject(ValidatingObject, SharedLoggingObject):

    name = Field(instance_of=string_types, optional=True, default=None)

    def __init__(self, **fields):
        super(ReferencingObject, self).__init__(**fields)
        if self.name is None:
            self.name = self.__class__.__name__
        SharedLoggingObject.__init__(self)

    def get_references(self, for_execution=False):
        refs = set()
        for k, v in self.__fields__.items():
            if isinstance(v, Reference) and (v.affects_execution_order or not for_execution):
                value = getattr(self, k)
                if isinstance(v, ReferenceList):
                    refs.update(value)
                elif value is not None:
                    refs.add(value)
        return refs

    def _find_attributes_for_reference(self, reference, for_execution=False):
        attribute_names = set()
        for k, v in self.__fields__.items():
            if isinstance(v, Reference) and (v.affects_execution_order or not for_execution):
                value = getattr(self, k)
                if (isinstance(v, ReferenceList) and reference in value) or value is reference:
                    attribute_names.add(k)
        return attribute_names

    @property
    def all_references(self):
        _, _, all_refs = self._get_reverse_mapping()
        return all_refs

    @property
    def all_execution_references(self):
        _, _, all_refs = self._get_reverse_mapping(for_execution=True)
        return all_refs

    def _get_reverse_mapping(self, parent_nodes=None, previously_seen_cache=None, for_execution=False, include_self=True):
        """
        Does the bulk of the work for walking the reference tree for all of the references and references for the node
        Does this recursively doing a depth-first search
        """
        if parent_nodes is None:
            parent_nodes = set()
            previously_seen_cache = dict()

        if self in previously_seen_cache:
            return previously_seen_cache[self]

        reference_consumers = defaultdict(set)
        all_references = set()
        lowest_level_references = set()

        references = self.get_references(for_execution=for_execution)

        if len(references) == 0:
            if include_self:
                lowest_level_references.add(self)
            previously_seen_cache[self] = (lowest_level_references, reference_consumers, all_references)
            return previously_seen_cache[self]

        elif len(parent_nodes) >= MAXIMUM_REFERENCE_DEPTH:
            raise ExceedsMaximumDepthError()

        parent_nodes.add(self)
        for reference in references:
            if not isinstance(reference, ReferencingObject):
                continue

            if reference in parent_nodes:
                error = CircularReferenceError(reference)
                error.add_reference(self, self._find_attributes_for_reference(reference, for_execution=for_execution))
                raise error

            try:
                ref_ll_references, ref_reference_consumers, ref_all_references = reference._get_reverse_mapping(parent_nodes, previously_seen_cache, for_execution)
            except CircularReferenceError as e:
                e.add_reference(self, self._find_attributes_for_reference(reference, for_execution=for_execution))
                raise e

            all_references.update(ref_all_references)
            lowest_level_references.update(ref_ll_references)
            for ref, ref_consumers in ref_reference_consumers.items():
                reference_consumers[ref].update(ref_consumers)

            if include_self:
                reference_consumers[reference].add(self)

        parent_nodes.remove(self)
        all_references.update(references)

        previously_seen_cache[self] = (lowest_level_references, reference_consumers, all_references)
        return previously_seen_cache[self]

    def reference_generations(self, for_execution=False):
        """
        Generator through generations of references, so each yield contains
        steps that can all be run in parallel with one another if the generations
        are run serially.  Useful for manually running nodes or visualization.
        """
        lowest_level_references, reference_consumers, _ = self._get_reverse_mapping()
        finished_references = set()
        while len(lowest_level_references) > 0:
            yield lowest_level_references
            finished_references.update(lowest_level_references)
            new_lowest_level_references = set()
            for reference in lowest_level_references:
                for consumer in reference_consumers[reference]:
                    con_unfinished_refs = consumer.get_references(for_execution=for_execution) - finished_references
                    if len(con_unfinished_refs) == 0:
                        new_lowest_level_references.add(consumer)
            lowest_level_references = new_lowest_level_references

    def __repr__(self):
        return '<{0.__class__.__name__}: {0.name}>'.format(self, )
