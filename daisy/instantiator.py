from daisy.executor import Executor
from daisy.step import Step
from daisy.field import Field
from daisy.constants import CLASS_KEY
from daisy.reference import Reference, ReferenceList
from daisy.importer import find_class

ANONYMOUS_SUFFIX = 'reference'


class Instantiator(Step):
    """
    Class that takes in a dictionary of <step_name, step_config> and instantiates them in the correct
    order to satisfy their references
    """
    config = Field(instance_of=dict)

    def __init__(self, **fields):
        super(Instantiator, self).__init__(**fields)
        self.steps = dict()

    def get_instantiation_steps(self):
        self.log('instantiator').debug("Creating Instantiation Steps")
        instantiation_steps_dict = dict()
        for step_name, step_config in self.config.items():
            step_config['name'] = step_name

            instantiation_step = InstantiationStep(step_config=step_config, creator=self)
            instantiation_steps_dict[step_name] = instantiation_step

        return instantiation_steps_dict

    def run(self):
        instantiation_steps = self.get_instantiation_steps()
        self.log('instantiator').debug("Linking reference dependencies")
        for step in instantiation_steps.values():
            step.evaluate_reference_dependencies(instantiation_steps)

        self.log('instantiator').debug("Running instantiator Tree")
        instantiation_executor = Executor(name=self.name)
        if self.root_log_id:
            instantiation_executor.root_log_id = self.root_log_id + '.' + instantiation_executor.root_log_id
        instantiation_executor.dependencies.update(set(instantiation_steps.values()))
        self.executor_output = instantiation_executor.execute()
        self.status.set_finished()


class InstantiationStep(Step):
    def __init__(self, step_config, creator, **fields):
        super(InstantiationStep, self).__init__(name=step_config['name'], **fields)
        self.step_config = step_config
        if CLASS_KEY not in step_config:
            raise KeyError("Step {0!r} does not specify a class".format(step_config))

        step_class_name = step_config.pop(CLASS_KEY)
        _, step_class = find_class(step_class_name)
        if step_class is None:
            raise KeyError("Could not find the class {!r}".format(step_class_name))

        self.step_class = step_class
        self.creator = creator
        self.result_instance = None

    def _create_anonymous_reference(self, name, step_config, instantiation_steps_dict):
        if name in instantiation_steps_dict:
            raise KeyError("When trying to name an anonymous reference, there was already a step by the same name: {!r}.  You may want to rename that step or the root of the anonymous reference for this step".format(name))
        step_config['name'] = name
        instantiation_step = InstantiationStep(step_config, creator=self.creator)
        instantiation_steps_dict[name] = instantiation_step
        instantiation_step.evaluate_reference_dependencies(instantiation_steps_dict)
        return instantiation_step

    def evaluate_reference_dependencies(self, instantiation_steps_dict):
        for reference_attr, reference in self.step_class._find_fields():
            if reference_attr in self.step_config and isinstance(reference, Reference):
                if isinstance(reference, ReferenceList):
                    assert isinstance(self.step_config[reference_attr], list), "{!r} is supposed to be a list of references but was {!r}".format(reference_attr, reference)
                    for element_index, element in enumerate(self.step_config[reference_attr]):
                        # Handle anonymous references
                        if isinstance(element, dict):
                            anonymous_ref_name = '.'.join([self.step_config['name'], reference_attr, str(element_index), ANONYMOUS_SUFFIX])
                            self._create_anonymous_reference(anonymous_ref_name, element, instantiation_steps_dict)
                            element = anonymous_ref_name
                            self.step_config[reference_attr][element_index] = anonymous_ref_name

                        if element not in instantiation_steps_dict:
                            raise KeyError("Step {0!r} references the step {1!r} through the parameter {2!r} but {1!r} doesn't exist".format(self.name, element, reference_attr))
                        self.dependencies.add(instantiation_steps_dict[element])
                else:
                    element = self.step_config[reference_attr]
                    if isinstance(element, dict):
                        anonymous_ref_name = '.'.join([self.step_config['name'], reference_attr, ANONYMOUS_SUFFIX])
                        self._create_anonymous_reference(anonymous_ref_name, element, instantiation_steps_dict)
                        element = anonymous_ref_name
                        self.step_config[reference_attr] = anonymous_ref_name

                    if element not in instantiation_steps_dict:
                        raise KeyError("Step {0!r} references the step {1!r} through the parameter {2!r} but {1!r} doesn't exist".format(self.name, element, reference_attr))

                    self.dependencies.add(instantiation_steps_dict[element])

    def run(self):
        self.log('instantiation').info("Instantiating with config {!r}".format(self.step_config))
        for reference_attr, reference in self.step_class._find_fields():
            if isinstance(reference, Reference) and reference_attr in self.step_config:
                ref_key = self.step_config.pop(reference_attr)
                if isinstance(reference, ReferenceList):
                    self.step_config[reference_attr] = [self.creator.steps[k] for k in ref_key]
                else:
                    self.step_config[reference_attr] = self.creator.steps[ref_key]

        self.creator.steps[self.name] = self.step_class(**self.step_config)

        self.status.set_finished()
