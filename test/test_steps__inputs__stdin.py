from daisychain.steps.inputs.system import StdIn, sys
from mock import patch


TEST_STRING = 'THIS STRING IS COMPLETELY UNIQUE AND WILL NOT EXIST EVER AGAIN ON STDIN'

def test_input_stdin():
    with patch('sys.stdin') as mock_stdin:
        mock_stdin.read.return_value = TEST_STRING
        i = StdIn()

        assert i.pending
        i.run()
        assert i.finished
        assert TEST_STRING == i.output
