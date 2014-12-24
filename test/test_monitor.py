import daisy.steps.monitor
import daisy.step
import daisy.executor

class MockStep(daisy.step.Step):
    def run(self):
        self.status.set_finished()

class MockMonitor(daisy.steps.monitor.Monitor):
    def __init__(self, error=None, **fields):
        super(MockMonitor, self).__init__(**fields)
        self.error = error
        self.checked = False

    def run(self):
        if not self.checked:
            self.checked = True
        else:
            raise RuntimeError("Monitor was checked twice")
        if self.error:
            raise self.error


def test_working_monitor_no_watches():
    m = MockMonitor(name='test')
    assert m.status.pending
    m.status.check()
    assert m.status.pending
    assert not m.checked
    m.validate()
    m.status.set_validated()
    m.status.check()
    assert m.status.validated
    assert not m.checked
    m.run()
    m.status.check()
    assert m.status.finished
    assert m.checked

def test_watching_single_step_no_dependencies():
    step = MockStep(name='test_step')
    m = MockMonitor(name='test', watches=[step])
    assert m.status.pending
    m.status.check()
    assert m.status.pending
    m.status.set_validated()
    m.status.check()
    assert m.status.running
    step.status.set_running()
    m.status.check()
    assert m.status.validated
    assert not m.checked
    m.run()
    m.status.check()
    assert m.status.validated
    step.status.set_finished()
    m.status.check()
    assert m.status.finished

def test_watching_step_with_dependency():
    step_dep = MockStep(name='test_step_dep')
    step = MockStep(name='test_step', dependencies=[step_dep])
    m = MockMonitor(name='test', watches=[step])
    assert m.status.pending
    m.validate()
    m.status.set_validated()
    m.status.check()
    assert m.status.running
    step_dep.status.set_running()
    m.status.check()
    assert m.status.running
    step_dep.status.set_finished()
    m.status.check()
    assert m.status.running
    assert not m.checked
    step.status.set_running()
    m.status.check()
    assert m.status.validated
    assert not m.checked
    m.run()
    assert m.checked
    m.status.check()
    assert m.status.validated
    step.status.set_finished()
    m.status.check()
    assert m.status.finished

def test_monitor_failing():
    m = MockMonitor(name='test', error=RuntimeError("MockMonitorError"))
    assert m.status.pending
    m.validate()
    m.status.set_validated()
    m.status.check()
    try:
        m.run()
        assert False, "Error should have been raised by 'run'"
    except RuntimeError as e:
        assert e == m.error

    step = MockStep(name='test_step')
    m = MockMonitor(name='test', error=RuntimeError("MockMonitorError"), watches=[step])
    assert m.status.pending
    m.validate()
    m.status.set_validated()
    m.status.check()
    assert m.status.running
    step.status.set_running()
    m.status.check()
    assert m.status.validated
    try:
        m.run()
        assert False, "Error should have been raised by 'run'"
    except RuntimeError as e:
        assert e == m.error


def test_failing_step():
    step = MockStep(name='test_step')
    m = MockMonitor(name='test', watches=[step])
    assert m.status.pending
    m.status.check()
    assert m.status.pending
    m.validate()
    m.status.set_validated()
    assert m.status.validated
    m.status.check()
    assert m.status.running
    step.status.set_running()
    m.status.check()
    assert m.status.validated
    m.run()
    assert m.checked
    m.checked = False
    step.status.set_failed(RuntimeError("Step Failed."))
    m.status.check()
    assert m.status.finished
    assert not m.checked

def test_failing_step_dependency():
    step_dep = MockStep(name='test_step_dep')
    step = MockStep(name='test_step', dependencies=[step_dep])
    m = MockMonitor(name='test', watches=[step])
    assert m.status.pending
    m.status.check()
    assert m.status.pending
    m.validate()
    m.status.set_validated()
    assert m.status.validated
    m.status.check()
    assert m.status.running
    step_dep.status.set_failed(RuntimeError("Step Failed."))
    m.status.check()
    assert m.status.finished
    assert not m.checked


def test_monitor_fails_with_watches_and_watch_all():
    try:
        s1 = MockStep(name='s1')
        m2 = MockMonitor(name='m2', watch_all=True, watches=[s1])
        assert False, "Should have thrown a ValueError if both watch_all and watches are set"
    except ValueError as e:
        pass

def test_monitor_with_executor_and_watch_all():
    s1 = MockStep(name='s1')
    s2 = MockStep(name='s2', dependencies=[s1])
    s2_1 = MockStep(name='s2_1', dependencies=[s1])
    s3 = MockStep(name='s3', dependencies=[s2])

    m1 = MockMonitor(name='m1')
    m2 = MockMonitor(name='m2', watch_all=True)
    executor = daisy.executor.Executor(dependencies=[s1, s2, s2_1, s3, m1, m2])
    executor.execute()
    assert set(m2.watches) == {s1, s2, s2_1, s3}

    m2 = MockMonitor(name='m2', watch_all=True, dependencies=[s1])
    executor = daisy.executor.Executor(dependencies=[s1, s2, s2_1, s3, m1, m2])
    executor.execute()
    assert set(m2.watches) == {s2, s2_1, s3}

    m2 = MockMonitor(name='m2', watch_all=True, dependencies=[s2])
    executor = daisy.executor.Executor(dependencies=[s1, s2, s2_1, s3, m1, m2])
    executor.execute()
    assert set(m2.watches) == {s2_1, s3}

    m2 = MockMonitor(name='m2', watch_all=True, dependencies=[s2_1, s3])
    executor = daisy.executor.Executor(dependencies=[s1, s2, s2_1, s3, m1, m2])
    executor.execute()
    assert set(m2.watches) == set()
    assert not m2.watch_all


def test_monitor_with_executor_abort():
    m1 = MockMonitor(name='m1')
    m1.executor = daisy.executor.Executor(execution=daisy.executor.Execution())
    m1.executor.execution.aborted = True
    assert m1.status.pending
    m1.status.check()
    assert m1.status.finished
    assert not m1.checked

def test_monitor_starter():
    m1 = MockMonitor(name='m1')
    m_starter = daisy.steps.monitor.MonitorStarter(monitors=[m1])
    m1.watches.append(m_starter)
    executor = daisy.executor.Executor(dependencies=[m1, m_starter])
    assert m_starter.status.pending
    assert m1.status.pending
    executor.execute()
    assert m_starter.status.finished
    assert m1.status.finished

def test_monitor_starter_with_failed_monitor():
    m1 = MockMonitor(name='m1')
    m2 = MockMonitor(name='m2', dependencies=[m1])
    m1.status.set_failed(RuntimeError("MockMonitor failure"))
    m_starter = daisy.steps.monitor.MonitorStarter(monitors=[m1, m2])
    m1.watches.append(m_starter)
    executor = daisy.executor.Executor(dependencies=[m1, m_starter, m2], on_failure=daisy.executor.Executor.SKIP)
    assert m_starter.status.pending
    executor.execute()
    assert m_starter.status.failed
    assert m1.status.failed

