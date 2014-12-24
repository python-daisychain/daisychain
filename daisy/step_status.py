from threading import RLock


class CheckStatusException(Exception):
    def __init__(self, status, previous_stage, exception):
        super(CheckStatusException, self).__init__('{0.step!r} had an exception when checking its status: {1!r}'.format(status, exception))
        self.exception = exception
        self.status_ob = status
        self.previous_stage = previous_stage

    def revert(self):
        self.status_ob.stage = self.previous_stage


class StepStatus(object):
    PENDING = 'pending'
    RUNNING = 'running'
    VALIDATED = 'validated'
    FINISHED = 'finished'
    NOT_FAILED = {PENDING, RUNNING, VALIDATED, FINISHED}

    def __init__(self, stage=PENDING):
        super(StepStatus, self).__init__()
        self.stage = stage
        self.callback = None
        self.lock = RLock()
        self.step = None

    def set_pending(self):
        with self.lock:
            if self.step is not None:
                self.step.log('status.pending').info("Set to Pending")
            self.stage = self.PENDING

    def set_validated(self):
        with self.lock:
            if self.step is not None:
                self.step.log('status.validated').info("Set to Validated")
            self.stage = self.VALIDATED

    def set_running(self):
        with self.lock:
            if self.step is not None:
                self.step.log('status.running').info("Set to Running")
            self.stage = self.RUNNING

    def set_finished(self):
        with self.lock:
            if self.step is not None:
                self.step.log('status.finished').info("Set to Finished")
            self.stage = self.FINISHED

    def set_failed(self, exception=None):
        with self.lock:
            if self.step is not None:
                self.step.log('status.failed').exception("Step failed")
            self.stage = exception

    @property
    def pending(self):
        with self.lock:
            return self.stage == self.PENDING

    @property
    def running(self):
        with self.lock:
            return self.stage == self.RUNNING

    @property
    def validated(self):
        with self.lock:
            return self.stage == self.VALIDATED

    @property
    def finished(self):
        with self.lock:
            return self.stage == self.FINISHED

    @property
    def failed(self):
        with self.lock:
            return self.stage not in self.NOT_FAILED

    def check(self):
        if (self.pending or self.validated or self.running) and self.callback is not None:
            with self.lock:
                if self.step is not None:
                    self.step.log('status.check').debug("Checking status")
                try:
                    self.callback()
                except Exception as e:
                    wrapper_exception = CheckStatusException(self, self.stage, e)
                    self.set_failed(wrapper_exception)

    def __repr__(self):
        return "<{0.__class__.__name__} stage={0.stage!r}>".format(self)
