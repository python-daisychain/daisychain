from daisychain.step import Step
from daisychain.field import Field
from py3compat import string_types
from threading import Thread

class ThreadedStep(Step):

    def __init__(self, **fields):
        super(ThreadedStep, self).__init__(**fields)
        self._thread = Thread(target=self._exception_handled_run, name=self.name)
        self.status.callback = self.check_thread

    def _exception_handled_run(self):
        try:
            self.run()
        except Exception as e:
            self.status.set_failed(e)

    def check_thread(self):
        if (self.running or self.failed or self.finished) and not self._thread.is_alive():
            self._thread.join()
            if self.running:
                self.status.set_finished()

    def start(self):
        self.status.set_running()
        self._thread.start()
