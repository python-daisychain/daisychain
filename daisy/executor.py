from daisy.step import Step
from daisy.step_status import CheckStatusException
from daisy.steps.input import ConsoleInput
from daisy.log import get_logger
from daisy.reference import ReferenceList, ReferencingObject
import time


class ExecutorAborted(Exception):
    pass


class Execution(object):
    """
    Data structure for holding status of an execution
    """
    def __init__(self, executor=None):
        self.working_set = set()
        self.failed_steps = set()
        self.finished_steps = set()
        self.consumer_dict = {}
        self.all_refs = set()
        self.aborted = False
        self.updated = False
        self.executor = executor
        if executor is not None:
            self.working_set, self.consumer_dict, self.all_refs = executor._get_reverse_mapping(for_execution=True, include_self=False)
            for step in self.all_refs:
                step.executor = executor
                step.root_log_id = executor.root_log_id

    def consider_step_finished(self, step):
        self.finished_steps.add(step)
        self.working_set.remove(step)
        self.updated = True

    def consider_step_failed(self, step):
        self.failed_steps.add(step)
        self.working_set.remove(step)
        self.updated = True

    def add_consumers_to_working_set(self, step):
        for consumer in self.consumer_dict.get(step, set()):
            if len(consumer.get_references(for_execution=True) - self.finished_steps) == 0:
                self.working_set.add(consumer)
                self.updated = True


class Executor(ReferencingObject):
    GRACEFUL_SHUTDOWN = 'graceful shutdown'
    SKIP = 'skip'
    PROMPT = 'prompt'
    RAISE = 'raise'

    dependencies = ReferenceList(elements_of=Step, optional=True)

    def __init__(self, on_failure=RAISE, user_input_class=ConsoleInput, execution=None, scan_interval=0.0, dry_run=False, **fields):
        super(Executor, self).__init__(**fields)
        self.dependencies = set(self.dependencies)

        self.root_log_id = self.name
        if on_failure not in (self.GRACEFUL_SHUTDOWN, self.SKIP, self.PROMPT, self.RAISE):
            raise ValueError("on_failure must be one of Executor.SKIP, Executor.RAISE, Executor.PROMPT, Executor.GRACEFUL_SHUTDOWN")

        self.on_failure = on_failure
        self.user_input_class = user_input_class
        self.execution = execution
        self.scan_interval = scan_interval
        self.dry_run = dry_run

    def log(self, stream=None):
        stream_pieces = [r for r in [self.root_log_id, stream] if r is not None]
        log_stream = '.'.join(stream_pieces).strip('.')
        return get_logger(log_stream)

    def prompt_user_for_step(self, step, prompt, exception=None, valid_choices=None, default=None, abort_choice_if_previously_aborted=True):
        if abort_choice_if_previously_aborted and self.execution is not None and self.execution.aborted:
            self.log().debug("Automatically Aborting prompt for {0.name} because of previous abort".format(step))
            raise ExecutorAborted("Executor previously aborted")

        critical_notification = "Need user input_step for {0.name!r}".format(step)

        if exception:
            exception_message = "Exception: {0!s}".format(exception)
        else:
            exception_message = None

        full_prompt = "\n\n".join([piece for piece in [critical_notification, exception_message, prompt] if piece is not None])
        input_step = self.user_input_class(name=step.name, prompt=full_prompt, valid_choices=valid_choices, default=default)
        input_step.prompt_user()
        return input_step.output

    def execute(self):
        """
        Runs a validation execution which, if 'self.dry_run' is not set, will be followed by a full execution
        """

        if self.execution is None:
            self.execution = Execution(executor=self)

        self.log().info("Validating plan...")
        self._run_execution(for_validation=True)
        if self.execution.aborted:
            self.log().error("Plan failed to validate.")
        else:
            self.log().info("Plan successfully validated.")
            if self.dry_run:
                self.log().info("Execution is in 'dry-run' mode so steps are not run")
            else:
                self.log().info("Beginning execution...")
                self.execution = Execution(executor=self)
                self._run_execution()

        return self.execution

    def _validate_step(self, step):
        if step.status.pending:
            try:
                step.validate()
                if step.status.pending:
                    step.status.set_validated()
            except Exception as e:
                step.status.set_failed(e)

        if step.status.failed:
            raise step.status.stage

    def _execute_step(self, step):
        try:
            self.log('execution').debug("Checking status of {0.name}".format(step))
            step.status.check()
            self.log('execution').debug("Status of {0.name}: {0.status.stage}".format(step))
        except Exception as e:
            step.status.set_failed(CheckStatusException(step.status, previous_stage=step.status.stage, exception=e))
            raise step.status.stage

        if step.status.running:
            # Step is still running so don't interact with it
            return

        elif step.status.finished:
            self.execution.consider_step_finished(step)
            if not self.execution.aborted:
                self.execution.add_consumers_to_working_set(step)

        elif step.status.pending or step.status.validated:
            if self.execution.aborted:
                self.execution.working_set.remove(step)
                self.execution.updated = True
                return

            try:
                if step.status.pending:
                    self._validate_step(step)
                else:
                    step.run()
            except Exception as e:
                step.status.set_failed(e)
                raise

        else:
            raise step.status.stage

    def _handle_step_failure(self, step):
        if self.on_failure in (self.RAISE, self.GRACEFUL_SHUTDOWN):
            self.execution.aborted = True

        if self.on_failure == self.RAISE:
            raise step.status.stage

        elif self.on_failure in (self.SKIP, self.GRACEFUL_SHUTDOWN):
            self.execution.consider_step_failed(step)

        elif self.on_failure == self.PROMPT:
            step.prompt_user_for_status(exception=step.status.stage)


    def _run_execution(self, for_validation=False):
        """
        Executes all of the dependencies of the executor starting at the lowest-level references and moving up the dependency tree.
        if 'for_validation' is True, it specifically skips the 'run' phase of the steps so that all of the steps can be validated before being
        run
        """
        if for_validation:
            execution_type = 'validation'
        else:
            execution_type = 'execution'

        while self.execution.working_set:
            self.execution.updated = False
            for step in list(self.execution.working_set):
                with step.status.lock:
                    try:
                        if for_validation:
                            if not self.execution.aborted:
                                self._validate_step(step)
                            self.execution.consider_step_finished(step)
                            if not self.execution.aborted:
                                self.execution.add_consumers_to_working_set(step)
                        else:
                            self._execute_step(step)

                    except Exception as e:
                        step.status.set_failed(e)
                        self._handle_step_failure(step)

            if self.execution.updated:
                self.log(execution_type).info("Step status update: {}/{} finished. {} in-flight. {} failed.".format(len(self.execution.finished_steps),
                                                                                                  len(self.execution.all_refs),
                                                                                                  len(self.execution.working_set),
                                                                                                  len(self.execution.failed_steps)))

            if self.scan_interval > 0 and self.execution.working_set and not for_validation:
                self.log(execution_type).debug("Sleeping {!s} seconds before next run".format(self.scan_interval))
                time.sleep(self.scan_interval)

        if self.execution.aborted:
            self.log(execution_type).error("Aborted prematurely")
        elif self.execution.failed_steps:
            self.log(execution_type).info("Finished all steps but some had errors that were skipped.")
        else:
            self.log(execution_type).info("Finished all steps successfully")
