from daisy.step import Step
from daisy.reference import Reference
from daisy.steps.input import Input


class Output(Step):
    """
    Generic step for writing or sending the output from an Input step
    """
    input_step = Reference(instance_of=Input)
