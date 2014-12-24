from daisychain.steps.outputs.file import OutputFile
from daisychain.steps.input import InMemoryInput
import tempfile
import os

TEST_STRING = 'THIS OUTPUT STRING IS COMPLETELY UNIQUE AND WILL NOT EXIST EVER AGAIN'

def test_output_file():
    t = tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), delete=False)
    t.close()

    try:
        i = OutputFile(path=t.name, input_step=InMemoryInput(output=TEST_STRING))
        assert i.pending
        i.run()
        assert i.finished
        with open(t.name) as f:
            assert TEST_STRING in f.read()
    finally:
        if os.path.exists(t.name):
            os.unlink(t.name)

def test_output_failure():
    i = OutputFile(path='/thisdirectoryreallydoesnotexist', input_step=InMemoryInput(output=TEST_STRING))
    assert i.pending
    try:
        i.run()
    except Exception as e:
        pass
    else:
        assert False, "Trying to output to a directory that doesn't exist should fail"
