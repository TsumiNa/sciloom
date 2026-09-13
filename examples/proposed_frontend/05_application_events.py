"""Design example: application/event semantic roles."""

from sciloom import Application, Var, main, on_error, on_start, on_stop


class PolymerizationApplication(Application):
    error_latched: Var[bool] = False

    @on_start
    def initialize(self):
        initialize_safe_states()

    @main
    def run(self):
        execute_polymerization_workflow()

    @on_error
    def error(self, ErrorMessage):
        log(ErrorMessage)
        alert_maintenance(ErrorMessage)
        set_safe_nonrobotic_states()

    @on_stop
    def stop(self):
        normal_shutdown()
