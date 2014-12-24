from daisy.steps.input import Input
from daisy.field import Field


class InputFile(Input):
    path = Field(instance_of=basestring)

    def run(self):
        with open(self.path) as f:
            self.output = f.read()
        self.status.set_finished()
