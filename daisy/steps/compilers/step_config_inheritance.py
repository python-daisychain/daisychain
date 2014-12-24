from daisy.step import Step
from daisy.executor import Executor
from daisy.steps.compiler import Compiler
from daisy.constants import STEPS_KEY
from py3compat import string_types


class StepConfigInheritance(Compiler):

    class ParentedConfigurationStep(Step):
        PARENT_KEYWORD = '__super__'

        def __init__(self, step_config, **fields):
            super(StepConfigInheritance.ParentedConfigurationStep, self).__init__(**fields)
            self.step_config = step_config
            self.parent_step_names = self.step_config.pop(self.PARENT_KEYWORD, list())
            if isinstance(self.parent_step_names, string_types):
                self.parent_step_names = [self.parent_step_names]
            self.parenting_steps = None

        def evaluate_parentage(self, parenting_steps):
            self.parenting_steps = parenting_steps
            for parent_step_name in self.parent_step_names:
                if parent_step_name not in self.parenting_steps:
                    raise KeyError("{!r} is supposed to inherit from the step {!r} but there is no step by that id".format(self.name, parent_step_name))
                parent_step = parenting_steps[parent_step_name]
                self.dependencies.add(parent_step)

        def run(self):
            for parent_step_name in self.parent_step_names:
                parent_config = self.parenting_steps[parent_step_name].step_config
                for key, value in parent_config.items():
                    if key not in self.step_config:
                        self.step_config[key] = value
            self.status.set_finished()

    def compile(self, config):
        parenting_steps = dict()
        executor = Executor(name=self.name)
        for step_name, step_config in config[STEPS_KEY].items():
            parenting_steps[step_name] = StepConfigInheritance.ParentedConfigurationStep(step_config, name=step_name)

        executor.dependencies.update(set(parenting_steps.values()))

        for parenting_step in list(parenting_steps.values()):
            parenting_step.evaluate_parentage(parenting_steps)

        executor.execute()
        return config
