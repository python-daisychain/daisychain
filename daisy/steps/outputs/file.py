from daisy.steps.output import Output
from daisy.field import Field


class OutputFile(Output):
    path = Field(instance_of=basestring)

    def run(self):
        with open(self.path, 'w') as f:
            f.write(self.input_step.output)
        self.status.set_finished()
