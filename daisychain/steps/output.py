from daisychain.step import Step
from daisychain.reference import Reference
from daisychain.steps.input import Input


class Output(Step):
    """
    Generic step for writing or sending the output from an Input step
    """
    input_step = Reference(instance_of=Input)
