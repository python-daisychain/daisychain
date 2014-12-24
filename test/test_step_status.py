from daisy.step_status import StepStatus, CheckStatusException

def test_status():
    s = StepStatus()
    assert s.pending
    assert not s.running
    assert not s.finished
    assert not s.failed
    assert s.callback is None
    assert s.stage is s.PENDING
    assert repr(s)

    s.set_running()
    assert not s.pending
    assert s.running
    assert not s.finished
    assert not s.failed
    assert s.callback is None
    assert s.stage is s.RUNNING

    s.set_finished()
    assert not s.pending
    assert not s.running
    assert s.finished
    assert not s.failed
    assert s.callback is None
    assert s.stage is s.FINISHED

    exception = RuntimeError('mock error')
    s.set_failed(exception=exception)
    assert not s.pending
    assert not s.running
    assert not s.finished
    assert s.failed
    assert s.callback is None
    assert s.stage is exception

    s.set_failed()
    assert not s.pending
    assert not s.running
    assert not s.finished
    assert s.failed
    assert s.callback is None
    assert s.stage is None


def test_callback():
    class MockStep(object):
        def __init__(self):
            self.status = StepStatus()
            self.status.callback = self.status_check

        def status_check(self):
            if self.status.pending:
                self.status.set_running()
            elif self.status.running:
                self.status.set_finished()
            else:
                raise TypeError("This is bad")

    step = MockStep()
    s = step.status
    assert s.pending
    assert not s.running
    assert not s.finished
    assert not s.failed
    assert s.stage is s.PENDING

    step.status.check()
    assert not s.pending
    assert s.running
    assert not s.finished
    assert not s.failed
    assert s.stage is s.RUNNING

    step.status.check()
    assert not s.pending
    assert not s.running
    assert s.finished
    assert not s.failed
    assert s.stage is s.FINISHED

    step.status.set_pending()
    def failing_check():
        raise RuntimeError("This is expected")
    step.status.callback = failing_check

    step.status.check()
    assert not s.pending
    assert not s.running
    assert not s.finished
    assert s.failed
    assert isinstance(s.stage, CheckStatusException)

    s.stage.revert()
    assert s.pending
    assert not s.running
    assert not s.finished
    assert not s.failed
    assert s.stage is s.PENDING
