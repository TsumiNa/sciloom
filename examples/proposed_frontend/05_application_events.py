"""Design example: application/event semantic roles."""

from sciloom import Application, Boolean, on_start, on_error, on_stop, main


class PolymerizationApplication(Application):
    error_latched: Boolean = False

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
