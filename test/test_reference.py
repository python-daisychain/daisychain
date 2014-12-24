from daisychain.reference import ReferencingObject, Reference, ReferenceList, CircularReferenceError, ExceedsMaximumDepthError, MAXIMUM_REFERENCE_DEPTH
import time


### Testing is mostly done on the Referencing Object since Reference only adds in the 'affects_execution_order' to a Field variable

class TestRef(ReferencingObject):
    ref = Reference(instance_of=ReferencingObject, optional=True)
    reflist = ReferenceList(elements_of=ReferencingObject, optional=True)
    any_object_ref = Reference(optional=True)
    non_exec_ref = Reference(optional=True, affects_execution_order=False)

    def create_mock_tree(self, layers, layer_size):
        for i in range(layer_size):
            r = TestRef(name='{}_{}'.format(self.name, i))
            self.reflist.append(r)
            if layers > 1:
                r.create_mock_tree(layers - 1, layer_size)

def test_no_references():
    t = TestRef(name='t')
    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]

def test_single_reference():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.reflist == list()
    assert t2.all_references == {t}
    for actual, expected in zip(list(t2.reference_generations()), [{t}, {t2}]):
        assert actual == expected

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]

def test_non_referencing_reference():
    t = TestRef(name='t', any_object_ref=5)
    t2 = TestRef(name='t2', ref=t)

    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.all_references == {t, 5}
    for actual, expected in zip(list(t2.reference_generations()), [{5}, {t}, {t2}]):
        assert actual == expected

    assert t.any_object_ref == 5
    assert t.get_references() == {5}
    assert t.all_references == {5}

def test_reference_affects_execution_order():
    t = TestRef(name='t', any_object_ref=5)
    t2 = TestRef(name='t2', non_exec_ref=t)
    assert t2.get_references() == {t}
    assert t2.non_exec_ref is t
    assert t2.all_references == {t, 5}
    assert t2.all_execution_references == set()

def test_reference_list_single_level():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', reflist=[t])
    assert t2.get_references() == {t}
    assert t2.ref is None
    assert t2.reflist == [t]
    assert t2.all_references == {t}
    for actual, expected in zip(list(t2.reference_generations()), [{t}, {t2}]):
        assert actual == expected

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]

def test_reference_3_levels():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', ref=t2)
    assert t3.get_references() == {t2}
    assert t3.ref is t2
    assert t3.reflist == list()
    assert t3.all_references == {t2, t}
    for actual, expected in zip(list(t3.reference_generations()), [{t}, {t2}, {t3}]):
        assert actual == expected

    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.reflist == list()
    assert t2.all_references == {t}
    for actual, expected in zip(list(t2.reference_generations()), [{t}, {t2}]):
        assert actual == expected

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]


def test_with_mixed_ref_and_reflist():
    t = TestRef(name='t')
    t2 = TestRef(name='t2')
    t3 = TestRef(name='t3', ref=t, reflist=[t2])
    assert t3.get_references() == {t, t2}
    assert t3.ref is t
    assert t3.reflist == [t2]
    assert t3.all_references == {t, t2}
    for actual, expected in zip(list(t3.reference_generations()), [{t, t2}, {t3}]):
        assert actual == expected

    assert t2.get_references() == set()
    assert t2.ref is None
    assert t2.reflist == list()
    assert t2.all_references == set()
    assert list(t2.reference_generations()) == [{t2}]

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]

def test_mixed_ref_and_reflist_with_redundant_ref():
    t = TestRef(name='t')
    t2 = TestRef(name='t2')
    t3 = TestRef(name='t3', ref=t, reflist=[t, t2])
    assert t3.get_references() == {t, t2}
    assert t3.ref is t
    assert t3.reflist == [t, t2]
    assert t3.all_references == {t, t2}
    for actual, expected in zip(list(t3.reference_generations()), [{t, t2}, {t3}]):
        assert actual == expected

    assert t2.get_references() == set()
    assert t2.ref is None
    assert t2.reflist == list()
    assert t2.all_references == set()
    assert list(t2.reference_generations()) == [{t2}]

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]


def test_shared_ref():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', ref=t)
    t4 = TestRef(name='t4', reflist=[t2, t3])

    assert t4.get_references() == {t2, t3}
    assert t4.ref is None
    assert t4.reflist == [t2, t3]
    assert t4.all_references == {t, t2, t3}
    for actual, expected in zip(list(t4.reference_generations()), [{t}, {t2, t3}, {t4}]):
        assert actual == expected


    assert t3.get_references() == {t}
    assert t3.ref is t
    assert t3.reflist == list()
    assert t3.all_references == {t}
    for actual, expected in zip(list(t3.reference_generations()), [{t}, {t3}]):
        assert actual == expected

    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.reflist == list()
    assert t2.all_references == {t}
    for actual, expected in zip(list(t2.reference_generations()), [{t}, {t2}]):
        assert actual == expected

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]


def test_share_ref_with_dependency():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', ref=t)
    t4 = TestRef(name='t4', ref=t, reflist=[t2, t3])

    assert t4.get_references() == {t, t2, t3}
    assert t4.ref is t
    assert t4.reflist == [t2, t3]
    assert t4.all_references == {t, t2, t3}
    for actual, expected in zip(list(t4.reference_generations()), [{t}, {t2, t3}, {t4}]):
        assert actual == expected


    assert t3.get_references() == {t}
    assert t3.ref is t
    assert t3.reflist == list()
    assert t3.all_references == {t}
    for actual, expected in zip(list(t3.reference_generations()), [{t}, {t3}]):
        assert actual == expected

    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.reflist == list()
    assert t2.all_references == {t}
    for actual, expected in zip(list(t2.reference_generations()), [{t}, {t2}]):
        assert actual == expected

    assert t.get_references() == set()
    assert t.ref is None
    assert t.reflist == list()
    assert t.all_references == set()
    assert list(t.reference_generations()) == [{t}]


def test_circular_reference():
    t = TestRef(name='t')
    t.ref = t
    assert t.get_references() == {t}
    assert t.ref is t
    assert t.reflist == list()
    try:
        t.all_references
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have thrown a CircularReferenceError"

def test_circular_reference_in_references():
    t = TestRef(name='t')
    t2 = TestRef(name='t2',ref=t)
    t.ref = t2
    assert t.get_references() == {t2}
    assert t.ref is t2
    assert t.reflist == list()
    assert t2.get_references() == {t}
    assert t2.ref is t
    assert t2.reflist == list()

    try:
        t2.all_references
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have thrown a CircularReferenceError"

    try:
        t.all_references
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have thrown a CircularReferenceError"


def test_circular_reference_in_subreferences():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', ref=t2)
    t.ref = t2
    for r in [t, t2, t3]:
        try:
            r.all_references
        except CircularReferenceError:
            pass
        else:
            assert False, "Should have thrown a CircularReferenceError"

def test_circular_reference_between_ref_attributes():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', reflist=[t2])
    t.ref = t3
    for r in [t, t2, t3]:
        try:
            r.all_references
        except CircularReferenceError:
            pass
        else:
            assert False, "Should have thrown a CircularReferenceError"

def test_circular_reference_3_deep():
    t = TestRef(name='t')
    t2 = TestRef(name='t2', ref=t)
    t3 = TestRef(name='t3', ref=t2)
    t4 = TestRef(name='t4', ref=t3)
    t.ref = t4
    for r in [t, t2, t3, t4]:
        try:
            r.all_references
        except CircularReferenceError:
            pass
        else:
            assert False, "Should have thrown a CircularReferenceError"

### From here I'm going to be building the trees in the reverse order because it's easier for instantiation

def test_circular_ref_cross_tree():
    t_1_2 = TestRef(name='t_1_2')
    t_1_1 = TestRef(name='t_1_1')
    t_1 = TestRef(name='t_1', reflist=[t_1_1, t_1_2])
    t_2_2_1 = TestRef(name='t_2_2_1')
    t_2_2 = TestRef(name='t_2_2', ref=t_2_2_1)
    t_2_1 = TestRef(name='t_2_1')
    t_2 = TestRef(name='t_2', reflist=[t_2_1, t_2_2])
    t = TestRef(name='t', reflist=[t_1, t_2])

    #circular dependencies
    t_1_2.ref = t_2_2_1
    t_2_2_1.ref = t_1

    # References not in circular dependecy
    t_1_1.all_references
    t_2_1.all_references

    # References in circular dependency
    for r in [t, t_1, t_1_2, t_2, t_2_2, t_2_2_1]:
        try:
            r.all_references
        except CircularReferenceError:
            pass
        else:
            assert False, "Should have thrown a CircularReferenceError"

def test_maximum_recursion_error():
    t = TestRef(name='t')
    t.create_mock_tree(layers=MAXIMUM_REFERENCE_DEPTH + 1, layer_size=1)
    try:
        t.all_references
    except ExceedsMaximumDepthError:
        pass
    else:
        assert False, "Should have raised the ExceedsMaximumDepthError"

def test_maximum_depth():
    t = TestRef(name='t')
    t.create_mock_tree(layers=MAXIMUM_REFERENCE_DEPTH - 2, layer_size=1)
    t.all_references

"""
def test_performance_tracing_1000_node_3_deep_tree():
    t = TestRef(name='t')
    t.create_mock_tree(layers=3, layer_size=10)

    start_time = time.time()
    t.all_references
    total_time = time.time() - start_time
    assert total_time < 1.0, "Took more than 1 second to trace this performance test"

def test_performance_8191_node_12_deep_tree():
    t = TestRef(name='t')
    t.create_mock_tree(layers=12, layer_size=2)

    start_time = time.time()
    t.all_references
    total_time = time.time() - start_time
    assert total_time < 1.0, "Took more than 1 second to trace this performance test"


def test_performance_deep_tree_with_one_overarching_step():
    sub_t = TestRef(name='sub_t')
    sub_t.create_mock_tree(layers=12, layer_size=2)
    t = TestRef(name='t')
    t.reflist += list(sub_t.all_references)

    start_time = time.time()
    t.all_references
    total_time = time.time() - start_time
    assert total_time < 1.0, "Took more than 1 second to trace this performance test"

def test_performance_maximum_depth():
    t = TestRef(name='t')
    t.create_mock_tree(layers=MAXIMUM_REFERENCE_DEPTH - 2, layer_size=1)

    start_time = time.time()
    t.all_references
    total_time = time.time() - start_time
    assert total_time < 1.0, "Took more than 1 second to trace this performance test"

"""
