from daisy.steps.wait import Wait
from daisy.executor import Executor
import time

def test_init():
    w = Wait(seconds=4321)
    assert w.start_time is None
    assert w.instructions is not None
    assert w.seconds == 4321

def test_run():

    w = Wait(seconds=0.1)
    executor = Executor(dependencies=[w], scan_interval=0.01)
    start_time = time.time()
    executor.execute()
    assert time.time() - start_time > 0.1

