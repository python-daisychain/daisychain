from daisy.steps.manual import Manual
from daisy.executor import Executor
from mock import patch
import py3compat
if py3compat.PY2:
    input_function = '__builtin__.raw_input'
else:
    import builtins
    input_function = 'builtins.input'

def test_manual_step():
    m = Manual(instructions='Do something')
    e = Executor(name='test_manual', dependencies=[m])
    with patch(input_function) as mock_raw_input:
        mock_raw_input.side_effect = ['f']
        e.execute()
    assert m.finished

def test_manual_step():
    m = Manual(instructions='Do something')
    e = Executor(name='test_manual', dependencies=[m])
    with patch(input_function) as mock_raw_input:
        mock_raw_input.side_effect = ['a']
        e.execute()
    assert m.failed

