from daisy.steps.output import Output
from daisy.field import Field
from py3compat import string_types


class OutputFile(Output):
    path = Field(instance_of=string_types)

    def run(self):
        with open(self.path, 'w') as f:
            f.write(self.input_step.output)
        self.status.set_finished()
