from daisy.steps.input import Input
from daisy.field import Field
from py3compat import string_types

class InputFile(Input):
    path = Field(instance_of=string_types)

    def run(self):
        with open(self.path) as f:
            self.output = f.read()
        self.status.set_finished()
