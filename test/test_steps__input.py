import daisy.steps.input
from mock import patch

import py3compat
if py3compat.PY2:
    input_function = 'daisy.steps.input.input'
else:
    import builtins
    input_function = 'builtins.input'

def test_inmemory_input():
    i = daisy.steps.input.InMemoryInput(output='abc')
    i.run()
    assert i.output == 'abc'
    assert i.status.finished

def test_console_input_success():
    with patch(input_function) as mock_raw_input:
        with patch('getpass.getuser') as mock_getuser:
            mock_raw_input.side_effect = ['r', '3', '', 'Y', '', 'n']
            mock_getuser.return_value = 'mockuser'
            i = daisy.steps.input.ConsoleInput(prompt='This is a (y)es/(n)o user input', valid_choices=['y','n'])
            i.prompt_user()
            assert i.output == 'y'
            assert i.user == 'mockuser'

            i.output = None
            i.prompt_user()
            assert i.output == 'n'
            assert i.user == 'mockuser'

            # choices that don't match with prompt
            mock_raw_input.side_effect = ['t', '', '6', 'r', 'y', 'N', '3']
            i = daisy.steps.input.ConsoleInput(prompt='This is a (y)es/(n)o user input', valid_choices=['r', '3'])
            i.prompt_user()
            assert i.output == 'r'
            assert i.user == 'mockuser'

            i.output = None
            i.prompt_user()
            assert i.output == '3'
            assert i.user == 'mockuser'

            # Autodetect choices
            mock_raw_input.side_effect = ['t', '', '6', 'r', 'y', 'N', '3']
            i = daisy.steps.input.ConsoleInput(prompt='This is a (y)es/(n)o user input')
            i.prompt_user()
            assert i.output == 'y'
            assert i.user == 'mockuser'

            i.output = None
            i.prompt_user()
            assert i.output == 'n'
            assert i.user == 'mockuser'

            # test default
            mock_raw_input.side_effect = ['t', '6', '']
            i = daisy.steps.input.ConsoleInput(prompt='This is a (y)es/(n)o user input', default='n')
            i.prompt_user()
            assert i.output == 'n'
            assert i.user == 'mockuser'

def test_console_input_prompt_detection_failure():
    try:
        i = daisy.steps.input.ConsoleInput(prompt='This is an import with no obvious choice input')
    except ValueError:
        pass
    else:
        assert False, "Instantiation of a ConsoleInput with no parentheses-enclosed choices shoulf raise a ValueError"
