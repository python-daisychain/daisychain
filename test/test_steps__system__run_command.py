from daisychain.steps.system.run_command import RunCommand, subprocess
from daisychain.steps.authentication.basic_auth import BasicAuth
from daisychain.executor import Executor
from subprocess import Popen as RealPopen

from mock import patch, MagicMock

def test_basic_command():
    c = RunCommand(command='ls -l', poll_interval_seconds=0)
    assert 'ls -l' in c.instructions
    executor = Executor(dependencies=[c])
    executor.execute()

def test_fail_sudo_without_auth():
    try:
        with patch('subprocess.Popen') as MockPopen:
            instance = MockPopen.return_value
            instance.poll.return_value = 0
            stdin = instance.stdin.return_value
            stdin.write.return_value = None
            stdin.close.return_value = None

            c = RunCommand(command='sudo -k mount -a')
    except TypeError:
        pass
    else:
        assert False, 'TypeError should have been raised when auth is not passed to a command with sudo'

def test_auth_command():
    with patch('subprocess.Popen') as MockPopen:
        validate_mock, auth_validate_mock, command_mock = MagicMock(spec=RealPopen)(), MagicMock(spec=RealPopen)(), MagicMock(spec=RealPopen)()
        MockPopen.side_effect = [validate_mock, auth_validate_mock, command_mock]
        validate_mock.returncode = 0
        validate_mock.communicate.return_value = (None, None)
        auth_validate_mock.returncode = 0
        auth_validate_mock.communicate.return_value = (None, None)
        command_mock.poll.return_value = 0
        stdin = command_mock.stdin.return_value
        stdin.write.return_value = None
        stdin.close.return_value = None

        auth = BasicAuth(username='mockuser', password='mockpassword')
        c = RunCommand(command='sudo -k mount -a', authentication=auth, poll_interval_seconds=0)

        executor = Executor(dependencies=[c])
        executor.execute()
        assert validate_mock.communicate.call_count == 1
        auth_validate_mock.communicate.assert_called_once_with('mockpassword\n')
        assert command_mock.poll.call_count == 1
        command_mock.stdin.write.assert_called_once_with('mockpassword\n')
        assert command_mock.stdin.close.call_count == 1

def test_failing_command():
    with patch('subprocess.Popen') as MockPopen:
        validate_mock, command_mock = MagicMock(spec=RealPopen)(), MagicMock(spec=RealPopen)()
        MockPopen.side_effect = [validate_mock, command_mock]
        validate_mock.returncode = 0
        command_mock.poll.return_value = 1
        stdin = command_mock.stdin.return_value
        stdin.write.return_value = None
        stdin.close.return_value = None

        c = RunCommand(command='ls -l', poll_interval_seconds=0)
        executor = Executor(dependencies=[c])
        try:
            executor.execute()
        except subprocess.CalledProcessError:
            pass
        except Exception as e:
            assert False, "Exception was supposed to be a CalledProcessError but was {!r} instead".format(e)
        else:
            assert False, "Exception was not raised".format(e)

def test_cannot_find_command():
    with patch('subprocess.Popen') as MockPopen:
        instance = MockPopen.returnvalue
        instance.returncode = 1

        c = RunCommand(command='ls -l', poll_interval_seconds=0)
        executor = Executor(dependencies=[c])
        try:
            executor.execute()
        except RuntimeError:
            pass
        except Exception as e:
            assert False, "Exception was supposed to be a RuntimeError but was {!r} instead".format(e)
        else:
            assert False, "Exception was not raised".format(e)

def test_failing_auth_command():
    with patch('subprocess.Popen') as MockPopen:
        validate_mock, auth_validate_mock = MagicMock(spec=RealPopen)(), MagicMock(spec=RealPopen)()
        MockPopen.side_effect = [validate_mock, auth_validate_mock]
        validate_mock.returncode = 0
        validate_mock.communicate.return_value = (None, None)
        auth_validate_mock.returncode = 1
        auth_validate_mock.communicate.return_value = (None, None)

        auth = BasicAuth(username='mockuser', password='mockpassword')
        c = RunCommand(command='sudo -k mount -a', authentication=auth, poll_interval_seconds=0)

        executor = Executor(dependencies=[c])
        try:
            executor.execute()
        except RuntimeError:
            pass
        except Exception as e:
            assert False, "Exception was supposed to be a RuntimeError but was {!r} instead".format(e)
        else:
            assert False, "Exception was not raised".format(e)
        assert validate_mock.communicate.call_count == 1
        auth_validate_mock.communicate.assert_called_once_with('mockpassword\n')
