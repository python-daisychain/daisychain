from daisy.executor import Executor, Execution, ExecutorAborted, ConsoleInput, CheckStatusException
from . import test_step
from mock import patch
try:
    import builtins
    input_function = 'builtins.input'
except ImportError:
    input_function = '__builtin__.raw_input'

def test_init():
    e = Executor()
    assert e.scan_interval == 0.0
    assert e.execution is None
    assert e.user_input_class is ConsoleInput
    assert e.on_failure is Executor.RAISE

    e = Executor(on_failure=Executor.PROMPT, scan_interval=1.0)
    assert e.scan_interval == 1.0
    assert e.execution is None
    assert e.user_input_class is ConsoleInput
    assert e.on_failure is Executor.PROMPT

    try:
        e = Executor(on_failure='NOT_A_KNOWN_FAILURE_TYPE')
    except ValueError:
        pass
    else:
        assert False, "Should have thrown a Value Error for an unknown failure mode"

def test_attach_self_as_executor():
    e = Executor(name='test_executor')
    assert e.scan_interval == 0.0
    assert e.execution is None
    assert e.user_input_class is ConsoleInput
    assert e.on_failure is Executor.RAISE

    dep = test_step.MockStep(name='mock_step')
    e.dependencies.add(dep)
    e.execution = Execution(executor=e)

    assert dep.executor is e
    assert dep.root_log_id == e.root_log_id

def test_prompt_user_for_step():
    with patch(input_function) as mock_raw_input:
        dep = test_step.MockStep(name='mock_step', run_exception=RuntimeError('Exception while running step'))
        e = Executor(name='test_executor')
        global times_called
        times_called = 0
        def raw_input_output(*args, **kwargs):
            global times_called
            times_called += 1
            responses = ['y','','r','']
            prompt = kwargs.get('prompt', args[0])
            assert 'mock_step' in prompt
            assert 'Does this test work (y)/(n)?' in prompt
            return responses[times_called - 1]

        mock_raw_input.side_effect = raw_input_output
        assert e.prompt_user_for_step(step=dep, prompt='Does this test work (y)/(n)?') == 'y'
        assert e.prompt_user_for_step(step=dep, prompt='Does this test work (y)/(n)?', valid_choices=['d','r']) == 'r'
        assert e.prompt_user_for_step(step=dep, prompt='Does this test work (y)/(n)?', default='n') == 'n'

        e.execution = Execution()
        e.execution.aborted = True

        try:
            e.prompt_user_for_step(step=dep, prompt='Does this test work (y)/(n)?')
        except ExecutorAborted:
            pass
        else:
            assert False, 'Should have raised an ExecutorAborted exception if it was previously aborted'


def test_execute():
    dep = test_step.MockStep(name='mock_step')
    e = Executor(name='test_executor', dependencies=[dep])
    e.execute()

    assert dep.finished

    dep_named = test_step.MockStep(name='mock_step_named')
    dep = test_step.MockStep(name='mock_step', named_reference=dep_named)
    assert dep.named_reference is dep_named

    e = Executor(name='test_executor', dependencies=[dep])
    e.execute()

    assert dep_named.finished
    assert dep.finished

    dep_dep = test_step.MockStep(name='mock_step_dep')
    dep = test_step.MockStep(name='mock_step', dependencies=[dep_dep])
    assert dep.dependencies == {dep_dep}

    e = Executor(name='test_executor', dependencies=[dep])
    assert e.dependencies == {dep}
    e.execute()

    assert dep_named.finished
    assert dep.finished

    dep = test_step.MockStep(name='mock_step', run_exception=RuntimeError('Exception while running step'))
    e = Executor(name='test_executor', dependencies=[dep])
    try:
        e.execute()
    except RuntimeError:
        assert dep.failed
    else:
        assert False, "Should have thrown the error the step raised"

def test_execute_check_status_failure_in_step():
    dep = test_step.MockStep(name='mock_step', check_status_exception=TypeError("Exception while checking status"))
    e = Executor(name='test_executor', dependencies=[dep])
    try:
        e.execute()
    except CheckStatusException:
        assert dep.failed
    else:
        assert False, "Should have thrown a CheckStatusException on failure"

    dep = test_step.MockStep(name='mock_step', check_status_exception=TypeError("Exception while checking status"))
    dep2 = test_step.MockStep(name='mock_failing_step_parent', dependencies=[dep])
    e = Executor(name='test_executor', dependencies=[dep2])
    try:
        e.execute()
    except CheckStatusException:
        assert dep2.validated
        assert dep.failed
    else:
        assert False, "Should have thrown a CheckStatusException on failure"

    dep = test_step.MockStep(name='mock_step')
    def raise_error():
        raise RuntimeError("Exception while forwarding callback")

    dep.status.check = raise_error
    dep2 = test_step.MockStep(name='mock_failing_step_parent', dependencies=[dep])
    e = Executor(name='test_executor', dependencies=[dep2])
    try:
        e.execute()
    except CheckStatusException:
        assert dep2.validated
        assert dep.failed
    else:
        assert False, "Should have thrown a CheckStatusException on failure"

def test_execute_skip_failures():
    dep = test_step.MockStep(name='mock_sibling_step', run_exception=RuntimeError("test_run_exception"))
    dep2 = test_step.MockStep(name='mock_sibling_step2', run_exception=RuntimeError("test_run_exception"))
    successful_dep = test_step.MockStep(name='successful_dep')
    parent = test_step.MockStep(name='mock_parent_step', dependencies=[dep, dep2, successful_dep])
    assert parent.dependencies == {dep, dep2, successful_dep}
    successful_parent = test_step.MockStep(name='mock_successful_parent', dependencies=[successful_dep])
    e = Executor(name='test_executor', on_failure=Executor.SKIP, dependencies=[parent, successful_parent])
    e.execute()
    assert dep.failed
    assert dep2.failed
    assert successful_dep.finished
    assert parent.validated
    assert successful_parent.finished
    assert not e.execution.aborted

def test_execute_graceful_shutdown():
    dep = test_step.MockStep(name='mock_sibling_step', run_exception=RuntimeError("test_run_exception"))
    dep2 = test_step.MockStep(name='mock_sibling_step2')
    dep2.run = lambda self: None
    successful_dep = test_step.MockStep(name='successful_dep')
    parent = test_step.MockStep(name='mock_parent_step', dependencies=[dep, dep2, successful_dep])
    assert parent.dependencies == {dep, dep2, successful_dep}
    successful_parent = test_step.MockStep(name='mock_successful_parent', dependencies=[successful_dep])
    e = Executor(name='test_executor', on_failure=Executor.GRACEFUL_SHUTDOWN, dependencies=[parent, successful_parent])
    e.execute()
    assert dep.failed
    assert dep2.status.finished or dep2.status.validated
    assert successful_dep.status.finished or successful_dep.status.validated
    assert parent.validated
    assert successful_parent.validated
    assert e.execution.aborted

def test_execute_graceful_shutdown_with_already_aborted_execution():
    dep = test_step.MockStep(name='mock_sibling_step')
    dep2 = test_step.MockStep(name='mock_sibling_step2', run_exception=RuntimeError("test_run_exception"))
    successful_dep = test_step.MockStep(name='successful_dep')
    parent = test_step.MockStep(name='mock_parent_step', dependencies=[dep, dep2, successful_dep])
    assert parent.dependencies == {dep, dep2, successful_dep}
    successful_parent = test_step.MockStep(name='mock_successful_parent', dependencies=[successful_dep])
    e = Executor(name='test_executor', on_failure=Executor.GRACEFUL_SHUTDOWN, dependencies=[parent, successful_parent])
    e.execution = Execution(executor=e)
    e.execution.aborted = True
    e.execute()
    assert dep.status.pending
    assert dep2.status.pending
    assert successful_dep.status.pending
    assert parent.status.pending
    assert successful_parent.status.pending

def test_prompting_during_execution():
    with patch(input_function) as mock_raw_input:
        dep = test_step.MockStep(name='mock_step', run_exception=RuntimeError('Exception while running step'))
        e = Executor(name='test_executor', on_failure=Executor.PROMPT, dependencies=[dep])
        global times_called
        times_called = 0
        def raw_input_output(*args, **kwargs):
            global times_called
            times_called += 1
            if times_called == 1:
                return 'r'
            elif times_called == 2:
                return 'f'
            assert times_called <= 2, "Called raw_input too many times"

        mock_raw_input.side_effect = raw_input_output
        e.execute()
        assert dep.status.finished
        assert times_called == 2

def test_execute_dry_run():
    dep = test_step.MockStep(name='dep')
    assert not dep.checked_ready
    assert dep.status.pending
    e = Executor(dry_run=True,dependencies=[dep])
    e.execute()
    assert dep.status.validated
    assert not dep.ran_once
