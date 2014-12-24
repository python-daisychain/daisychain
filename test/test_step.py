from daisy.step import Step, CircularReferenceError, ExceedsMaximumDepthError, MAXIMUM_REFERENCE_DEPTH, CheckStatusException
from daisy.reference import Reference
from daisy.executor import Executor, Execution

class MockTestFailure(Exception):
    pass

class MockStep(Step):
    named_reference = Reference(instance_of=Step, optional=True)
    named_non_execution_reference = Reference(instance_of=Step, optional=True, affects_execution_order=False)

    def __init__(self, check_status_exception=None, run_exception=None, **references):
        super(MockStep, self).__init__(**references)
        self.status.callback = self.check_status
        self.checked_ready = False
        self.ran_once = False
        self.check_status_exception = check_status_exception
        self.run_exception = run_exception

    def check_status(self):
        if self.check_status_exception:
            raise self.check_status_exception

        if self.status.running:
            self.status.set_finished()
        elif self.status.finished:
            return
        elif self.ran_once:
            self.status.set_running()

    def validate(self):
        self.checked_ready = True

    def run(self):
        for reference in self.get_references(for_execution=True):
            assert reference.finished

        if self.run_exception:
            raise self.run_exception

        assert not self.ran_once
        self.ran_once = True

def test_init():
    t = MockStep(name='t')
    assert t.status.pending
    assert len(t.dependencies) == 0
    assert len(t.get_references()) == 0

def test_run():
    t = MockStep(name='t')
    t.status.check()
    assert t.pending
    t.run()
    assert t.ran_once
    t.status.check()
    assert t.running
    t.status.check()
    assert t.finished

def test_add_dependency():
    t = MockStep(name='t')
    dep = MockStep(name='dep')
    t.dependencies.add(dep)
    assert t.get_references() == {dep}
    assert dep.get_references() == set()

def test_prune():
    subdep = MockStep()
    dep = MockStep(dependencies=[subdep])
    t = MockStep(dependencies=[subdep, dep])

    assert t.dependencies == {subdep, dep}

    t.prune()

    assert t.dependencies == {dep}

def test_prune_beyond_maximum_depth():
    dep = MockStep()
    for i in range(MAXIMUM_REFERENCE_DEPTH + 10):
        dep = MockStep(dependencies=[dep])

    try:
        dep.all_references
    except ExceedsMaximumDepthError:
        pass
    else:
        assert False, "Should have exceeded the maximum depth on this call"

    try:
        dep.prune()
    except ExceedsMaximumDepthError:
        pass
    else:
        assert False, "Should have exceeded the maximum depth on this call"

def test_prune_circular_dependency():
    dep = MockStep()
    dep2 = MockStep(dependencies=[dep])
    dep.dependencies.add(dep2)

    try:
        dep.prune()
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have thrown a CircularReferenceError"

    dep.dependencies = {dep}
    try:
        dep.prune()
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have thrown a CircularReferenceError"

def test_mock_step_raises_when_not_all_deps_complete():
    dep = MockStep()
    dep2 = MockStep(dependencies=[dep])

    try:
        dep2.run()
    except AssertionError:
        pass
    else:
        assert False, "Expected an Assertion error to be raised when not all of the dependencies of MockStep are finished when it is run"

    dep2 = MockStep(named_reference=dep)
    try:
        dep2.run()
    except AssertionError:
        pass
    else:
        assert False, "Expected an Assertion error to be raised when not all of the dependencies of MockStep are finished when it is run"

    dep2 = MockStep(named_non_execution_reference=dep)
    dep2.run()
    dep2.status.check()
    assert dep2.running
    dep2.status.check()
    assert dep2.finished

def test_prompt_user_no_executor():
    s = MockStep()
    try:
        s.prompt_user("This prompt is just for testing (n)")
    except RuntimeError:
        pass
    else:
        assert False, "Expected a RuntimeError if the executor isn't set during prompt"

def test_prompt_user_for_status():
    s = MockStep()
    s.prompt_user_for_status()
    assert s.status.failed
    assert isinstance(s.status.stage, RuntimeError)

    def mock_prompt_user(response):
        def wrapper(*args, **kwargs):
           return response
        return wrapper

    s.executor = Executor()
    s.executor.execution = Execution()

    s.prompt_user = mock_prompt_user('f')
    s.prompt_user_for_status()
    assert s.status.finished

    s.prompt_user = mock_prompt_user('r')
    s.prompt_user_for_status()
    assert s.status.pending

    s.prompt_user = mock_prompt_user('a')
    s.prompt_user_for_status()
    assert s.status.failed
    assert isinstance(s.status.stage, RuntimeError)

    s.status.set_failed(TypeError("A different kind of error"))
    s.prompt_user_for_status(exception=s.status.stage)
    assert isinstance(s.status.stage, TypeError)

    s.prompt_user = mock_prompt_user('r')
    s.status.stage = CheckStatusException(s.status, previous_stage='mock_stage', exception=TypeError("Error during check status"))
    s.prompt_user_for_status(exception=s.status.stage)
    assert s.status.stage == 'mock_stage'

    s.prompt_user = mock_prompt_user('a')
    s.status.stage = CheckStatusException(s.status, previous_stage='mock_stage', exception=TypeError("Error during check status"))
    s.prompt_user_for_status(exception=s.status.stage)
    assert s.status.failed
    assert isinstance(s.status.stage, CheckStatusException)

    s.prompt_user = mock_prompt_user('f')
    s.status.stage = CheckStatusException(s.status, previous_stage='mock_stage', exception=TypeError("Error during check status"))
    s.prompt_user_for_status(exception=s.status.stage)
    assert s.status.stage != 'mock_stage'
    assert s.status.finished

    def mock_prompt_user_error(*args, **kwargs):
        raise TypeError("This error came from prompt_user")

    s.prompt_user = mock_prompt_user_error
    s.prompt_user_for_status()
    assert isinstance(s.status.stage, TypeError)

