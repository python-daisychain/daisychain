import getpass
from daisy.step import Step
from daisy.field import Field
from py3compat import string_types

try:
    import builtins
    raw_input = input
except ImportError:
    pass

class BasicAuth(Step):

    username = Field(instance_of=string_types, optional=True)
    password = Field(instance_of=string_types, optional=True)
    credentials_for = Field(instance_of=string_types, optional=True, default='')

    def __init__(self, **fields):
        super(BasicAuth, self).__init__(**fields)
        if self.username is None:
            self._should_get_username = True
        else:
            self._should_get_username = False

        if self.password is None:
            self._should_get_password = True
        else:
            self._should_get_password = False

        if self.credentials_for:
            self.credentials_for = " for " + self.credentials_for

    def validate(self):
        self.run()

    def run(self):
        if self._should_get_username:
            self.username = self.get_username()

        if self._should_get_password:
            self.password = getpass.getpass(prompt="{0.name}: Please provide your password{0.credentials_for}:".format(self))
        self.status.set_finished()

    def get_username(self):
        username = getpass.getuser()
        if not username:
            username = raw_input("{0.name}: Could not autodetect your username.  Please provide your username{0.credentials_for}: ".format(self))
        return username

def _fix_bases_if_requests_is_present():
    try:
        import requests.auth
        BasicAuth.__bases__ = (Step, requests.auth.HTTPBasicAuth)
    except ImportError:
        BasicAuth.__bases__ = (Step, )
    return BasicAuth

_fix_bases_if_requests_is_present()
