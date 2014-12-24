import copy
from abc import abstractmethod

from daisychain.steps.pipe import Pipe
from daisychain.field import Field


class Compiler(Pipe):
    """
    A Compiler is a step that takes in a config input_step reference which presents a 'output' attribute representing the
    configuration tree to process.  Has an abstract method 'compile' which takes in a copy of the uncompiled-config
    and should return the compiled configuration.
    """
    run_from_here = Field(instance_of=bool, optional=True, default=False)

    @abstractmethod
    def compile(self, config):
        """
        Abstract method for compiling the configuration.  Should return the resultant configuration.
        """

    def run(self):
        config = copy.deepcopy(self.input_step.output)
        self.output = self.compile(config)
        self.log().debug("Output Configuration: {!r}".format(self.output))
        self.status.set_finished()
