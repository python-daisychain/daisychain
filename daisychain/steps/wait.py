import daisychain.step
from daisychain.field import Field
import time


class Wait(daisychain.step.Step):
    """
    Sleeps for a minimum number of seconds
    """
    seconds = Field(instance_of=(float, int), validator=lambda x: x > 0)

    def __init__(self, **fields):
        super(Wait, self).__init__(**fields)
        self.start_time = None
        self.status.callback = self.check_status
        self.instructions = "Wait {0.seconds} seconds before proceeding".format(self)

    def check_status(self):
        """
        Keep checking elapsed seconds until waited more than specified seconds
        """
        if self.start_time is None:
            return

        elapsed_seconds = time.time() - self.start_time

        if (elapsed_seconds >= self.seconds):
            self.status.set_finished()
        else:
            self.status.set_running()

    def run(self):
        self.start_time = time.time()
