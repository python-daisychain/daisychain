from daisy.steps.output import Output
import sys


class StdOut(Output):

    def run(self):
        sys.stdout.write(self.input_step.output)
        self.status.set_finished()
