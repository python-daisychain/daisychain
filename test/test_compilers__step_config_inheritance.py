from daisy.steps.compilers.step_config_inheritance import StepConfigInheritance
from daisy.steps.input import InMemoryInput
from daisy.reference import CircularReferenceError

from .util import compare_trees

def test_no_op():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}}
    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, input_config)

def test_single_inheritance():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'__super__': 'step1', 'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2', 'param1': 'value1'}}}
    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)

def test_multiple_inheritance():
    input_config = {'steps':
                        {'step1': {'param1': 'value1'},
                         'step2': {'param2': 'value2', 'param1': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step3': {'__super__': ['step1', 'step2'], 'param3': 'value3'}
                    }}
    expected_output = {'steps':
                        {'step1': {'param1': 'value1'},
                         'step2': {'param2': 'value2', 'param1': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step3': {'param1': 'value1', 'param2': 'value2',  'param3': 'value3'}
                    }}

    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)

def test_multiple_tier_inheritance():
    input_config = {'steps':
                        {'step1': {'param1': 'value1'},
                         'step2': {'__super__': 'step1', 'param2': 'value2'},
                         'step3': {'__super__': 'step2', 'param3': 'value3'}
                    }}
    expected_output = {'steps':
                        {'step1': {'param1': 'value1'},
                         'step2': {'param1': 'value1', 'param2': 'value2'},
                         'step3': {'param1': 'value1', 'param2': 'value2',  'param3': 'value3'}
                    }}

    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)




def test_multiple_tier_inheritance_with_overrides():
    input_config = {'steps':
                        {'step1': {'param1': 'value1', 'param2': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step2': {'__super__': 'step1', 'param2': 'value2', 'param3': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step3': {'__super__': 'step2', 'param3': 'value3'}
                    }}
    expected_output = {'steps':
                        {'step1': {'param1': 'value1', 'param2': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step2': {'param1': 'value1', 'param2': 'value2', 'param3': 'SHOULD_BE_OVERRIDDEN_BY_CHILDREN'},
                         'step3': {'param1': 'value1', 'param2': 'value2',  'param3': 'value3'}
                    }}

    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)


def test_missing_parent():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'__super__': 'step3', 'param2': 'value2'}}}
    compiler_input = InMemoryInput(output=input_config)
    compiler = StepConfigInheritance(input_step=compiler_input)
    try:
        compiler.run()
    except KeyError:
        pass
    else:
        assert False, "KeyError was not raised when a step referenced a parent that didn't exist"

