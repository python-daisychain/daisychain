from daisychain.steps.compiler import Compiler
from daisychain.constants import DEPENDENCIES_KEY, STEPS_KEY


class SeparateDependencyTree(Compiler):
    DEPENDENCY_TREE_KEY = '__dependencies__'

    def compile(self, config):
        if self.DEPENDENCY_TREE_KEY in config:
            dependency_tree = config.pop(self.DEPENDENCY_TREE_KEY)
            for step_name, step_config in config[STEPS_KEY].items():
                if DEPENDENCIES_KEY in config[STEPS_KEY][step_name]:
                    raise ValueError("Cannot have a step config that specifies both a {!r} section and {!r} at the step level".format(self.DEPENDENCY_TREE_KEY, DEPENDENCIES_KEY))
                if step_name in dependency_tree:
                    config[STEPS_KEY][step_name][DEPENDENCIES_KEY] = dependency_tree[step_name]

        return config
