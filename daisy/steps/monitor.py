from daisy.step import Step
from daisy.step_status import StepStatus
from daisy.field import Field
from daisy.reference import Reference,ReferenceList
from abc import abstractmethod

class MonitorStatus(StepStatus):
    def __init__(self, *args, **kwargs):
        super(MonitorStatus, self).__init__(*args, **kwargs)
        self.has_been_run_once = False

    def set_validated(self):
        super(MonitorStatus, self).set_validated()
        self.has_been_run_once = False


class Monitor(Step):
    """
    A monitor is a specific kind of step that will call its 'run' method every time any
    of the steps that it watches are running.
    """

    watches = ReferenceList(elements_of=Step, optional=True, affects_execution_order=False)
    watch_all = Field(instance_of=bool, optional=True, default=False)

    def __init__(self, status=None, **fields):
        if status is None:
            status = MonitorStatus()
        super(Monitor, self).__init__(status=status, **fields)
        if self.watch_all and self.watches:
            raise ValueError("Cannot set 'watch_all' and 'watches' options together")
        self.status.callback = self.check_watched_steps

    def check_watched_steps(self):
        """
        Method that handles how the step behaves given the status of the steps it is watching
        and the status of the monitor in these priories

        1) If it has no watched steps, run check_monitor once and report status based on that
        2) If a watched step or any of its dependencies have failed, set finished so that it the execution can exit cleanly
        3) If a watched step or any of its dependencies are running, check the monitor, leaving itself as running
        4) If a watched step is pending, wait
        5) If all of the watched steps are finished, mark itself as finished
        """
        if self.executor and self.executor.execution and self.executor.execution.aborted:
            self.status.set_finished()
            return

        if self.status.pending:
            # Has to wait until it is validated before it can start monitoring
            return

        if self.executor and self.watch_all and len(self.watches) == 0:
            self.log().debug("Evaluating watch_all")
            _, _, all_execution_references = self._get_reverse_mapping(for_execution=True)
            for reference in self.executor.all_references:
                if reference not in all_execution_references and reference is not self.executor and not isinstance(reference, Monitor):
                    self.watches.append(reference)
            if len(self.watches) == 0:
                self.log().debug("Even though watch_all is set, there are no steps that are valid to watch.  Will still run once before exiting")
                self.watch_all = False

        if len(self.watches) == 0:
            if self.status.has_been_run_once:
                self.status.set_finished()
                return
            else:
                self.status.set_validated()
                self.status.has_been_run_once = True
                return

        status = self.get_watched_steps_status()
        if status.running:
            self.log().debug("{0.step} is running.  Monitor will Run".format(status))
            self.status.set_validated()
            return
        elif status.failed:
            self.log().debug("Marking monitor finished due to failure in watched step: {0.step}".format(status))
            self.status.set_finished()
            return
        elif status.finished:
            self.log().debug("All watched steps have completed.  Monitor exiting")
            self.status.set_finished()
            return
        elif status.pending or status.validated:
            self.log().debug("All watched steps are pending or validated but not running.  Skipping check")
            self.status.set_running()
            return

    def get_watched_steps_status(self):
        overall_status = None
        for step in self.watches:
            status = self._search_tree_for_failures(step)
            if status.failed:
                return status
            elif overall_status is None or status.running or overall_status.finished:
                overall_status = status
        return overall_status

    def _search_tree_for_failures(self, step):
        if step.status.pending:
            for dependency in step.dependencies:
                status = self._search_tree_for_failures(dependency)
                if status.failed:
                    return status
        return step.status


class MonitorStarter(Step):
    """
    Step for waiting until all monitors are running before marking itself finished
    """

    monitors = ReferenceList(elements_of=Monitor, affects_execution_order=False)

    def __init__(self, **fields):
        super(MonitorStarter, self).__init__(**fields)
        self.monitors = set(self.monitors)

    def run(self):
        failed_monitors = self.monitors & self.executor.execution.failed_steps
        remaining_monitors = self.monitors - (self.executor.execution.working_set | self.executor.execution.finished_steps)
        if len(failed_monitors) > 0:
            self.status.set_failed(list(failed_monitors)[0].status.stage)
        elif len(remaining_monitors) == 0:
            self.status.set_finished()
