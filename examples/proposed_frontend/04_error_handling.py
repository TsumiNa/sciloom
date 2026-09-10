"""Design example: fatal AutoSuite faults versus recoverable result-style errors."""

from sciloom import Function, Input, Zone, Integer, AutoSuiteError, runtime


class LoadAndReact(Function):
    reactor: Input[Zone]
    csv_status: Integer = 0

    @runtime
    def run(self):
        # Recoverable/result-style operation: target primitive exposes a status code.
        self.csv_status = import_csv("conditions.csv")
        if self.csv_status != 0:
            log("CSV import failed")
            return

        # Fatal hardware operation: handler adds pre-stop actions, then propagates.
        try:
            load_reagents(self.reactor)
            start_reaction(self.reactor)
        except AutoSuiteError as err:
            log(err)
            alert_maintenance(err)
            raise
