import daisy.step


class Manual(daisy.step.Step):
    def __init__(self, instructions, **fields):
        super(Manual, self).__init__(**fields)
        self.instructions = """MANUAL STEP: This must be done manually by the operator.

=================== INSTRUCTIONS ===================

{}

================ END OF INSTRUCTIONS ===============
""".format(instructions)

    def run(self):
        self.log().debug("Prompting User")
        self.prompt_user_for_status(self.instructions + "\nPlease mark this step as finished once done.")
