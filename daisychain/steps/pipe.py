from daisychain.steps.input import Input
from daisychain.steps.output import Output


class Pipe(Output, Input):
    """
    A Pipe is a step that takes in the 'output' from a passed in 'step_input' and transforms it for consumption,
    presenting its own 'output' attribute for consumption in its run method
    """
    def __init__(self, **fields):
        super(Pipe, self).__init__(**fields)
        self.output = None
