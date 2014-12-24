from daisychain.steps.outputs.system import StdOut, sys
from daisychain.steps.input import InMemoryInput
from mock import patch
from py3compat import StringIO

TEST_STRING = 'THIS OUTPUT STRING IS COMPLETELY UNIQUE AND WILL NOT EXIST EVER AGAIN'

@patch('sys.stdout', new_callable=StringIO)
def test_output_stdout(mock_stdout):
    i = StdOut(input_step=InMemoryInput(output=TEST_STRING))
    assert i.pending
    i.run()
    assert i.finished
    assert mock_stdout.getvalue() == TEST_STRING
