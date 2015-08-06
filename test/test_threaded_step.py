from daisychain.threaded_step import ThreadedStep
from daisychain.executor import Executor
from daisychain.field import Field
import time


class ThreadedWait(ThreadedStep):
    seconds = Field(instance_of=(int, float), default=0.5)

    def run(self):
        time.sleep(self.seconds)

def test_init():
    w = ThreadedWait(seconds=4321)
    assert w.seconds == 4321
    assert w._thread is not None

def test_run():
    w = ThreadedWait(seconds=0.5)
    w2 = ThreadedWait(seconds=0.5)
    executor = Executor(dependencies=[w, w2], scan_interval=0.01)
    start_time = time.time()
    executor.execute()
    assert 0.5 < time.time() - start_time < 1.0

def test_error():
    w = ThreadedWait(seconds=-1)
    w.start()
    for i in range(10):
        if not w.running:
            break
        time.sleep(0.01)
    assert w.failed
