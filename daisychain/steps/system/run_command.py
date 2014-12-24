import subprocess
import shlex
import os
from daisychain.step import Step
from daisychain.field import Field
from daisychain.reference import Reference
from daisychain.steps.authentication.basic_auth import BasicAuth
from daisychain.decorators import cache_for
from py3compat import string_types


class RunCommand(Step):
    DEV_NULL = open('/dev/null', 'a')
    authentication = Reference(optional=True, instance_of=BasicAuth)
    command = Field(instance_of=string_types + (list,))
    poll_interval_seconds = Field(instance_of=(int, float), optional=True, default=1)

    def __init__(self, **fields):
        super(RunCommand, self).__init__(**fields)

        if isinstance(self.command, string_types):
            self.command = shlex.split(str(self.command))

        self.log().debug("Command to be run: {!r}".format(self.command))
        if os.path.basename(self.command[0]) == 'sudo' and os.getuid() != 0:
            if self.authentication is None:
                raise TypeError("{0.__class__.__name__}:{0.name!r} did not specify the required 'authentication' reference when using 'sudo'".format(self))
            else:
                self._forward_auth = True
        else:
            self._forward_auth = False
        self.status.callback = cache_for(seconds=self.poll_interval_seconds)(self.check_process)
        self.status.process = None

    def check_process(self):
        if self.status.running:
            return_code = self.status.process.poll()

            if return_code == 0:
                self.status.set_finished()
            elif return_code is not None:
                self.status.set_failed(subprocess.CalledProcessError(returncode=return_code, cmd=self.command))

    def validate(self):
        p = subprocess.Popen(['which', self.command[0]], stdout=self.DEV_NULL, stderr=self.DEV_NULL)
        p.communicate()
        if p.returncode != 0:
            raise RuntimeError("Could not find command using 'which {}'".format(self.command[0]))

        if self._forward_auth:
            p = subprocess.Popen(['sudo','-S','/bin/true'], stdin=subprocess.PIPE)
            p.communicate(str(self.authentication.password) + '\n')
            if p.returncode != 0:
                raise RuntimeError("Could not validate authentication credentials for sudo")
        self.status.set_validated()

    def run(self):
        command = self.command[:]
        if self._forward_auth:
            command.insert(1, '-S')
        self.status.process = subprocess.Popen(command, stdout=self.DEV_NULL, stderr=self.DEV_NULL, stdin=subprocess.PIPE)
        if self._forward_auth:
            self.status.process.stdin.write(str(self.authentication.password) + '\n')
            self.status.process.stdin.close()
        self.status.set_running()

    @property
    def instructions(self):
        return "\nRun this command from the command-line:\n\n{0}".format(' '.join(self.command))
