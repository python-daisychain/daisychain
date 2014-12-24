import daisy.steps.authentication.basic_auth
from mock import patch
import sys
import mock_requests
import mock_requests.auth
try:
    import builtins
    input_function = 'builtins.input'
except ImportError:
    input_function = '__builtin__.raw_input'



def run_with_basic_auth(BasicAuth):

    with patch('daisy.steps.authentication.basic_auth.getpass') as mock_getpass:
        with patch(input_function) as mock_raw_input:
            b = BasicAuth()
            assert b.username is None
            assert b.password is None

            mock_getpass.getuser.return_value = 'mockuser'
            mock_getpass.getpass.return_value = 'mockpassword'

            b.run()
            assert b.username == 'mockuser'
            assert b.password == 'mockpassword'

            mock_raw_input.return_value = 'mockuser2'
            mock_getpass.getuser.return_value = None
            mock_getpass.getpass.return_value = 'mockpassword2'

            b.run()
            assert b.username == 'mockuser2'
            assert b.password == 'mockpassword2'

            mock_getpass.getuser.side_effect = RuntimeError("This should never be called")
            mock_getpass.getpass.side_effect = RuntimeError("Neither should this")


            b = BasicAuth(username='mockuser3', password='mockpassword3', credentials_for='LDAP')
            assert 'LDAP' in b.credentials_for

            b.run()

            assert b.username == 'mockuser3'
            assert b.password == 'mockpassword3'

def test_basic_auth():
    run_with_basic_auth(daisy.steps.authentication.basic_auth.BasicAuth)

def test_basic_auth_with_requests():
    sys.modules['requests'] = mock_requests
    sys.modules['requests.auth'] = mock_requests.auth
    try:
        basic_auth_class = daisy.steps.authentication.basic_auth._fix_bases_if_requests_is_present()
        assert isinstance(basic_auth_class(), mock_requests.auth.HTTPBasicAuth)
        run_with_basic_auth(basic_auth_class)
    finally:
        sys.modules.pop('requests', None)
        sys.modules.pop('requests.auth', None)
        daisy.steps.authentication.basic_auth._fix_bases_if_requests_is_present()
