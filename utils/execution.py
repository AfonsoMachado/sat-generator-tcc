class ExecutionState:
    def __init__(self) -> None:
        self.running = False
        self.stop_requested = False

    def start(self) -> None:
        self.running = True
        self.stop_requested = False

    def stop(self) -> None:
        self.running = False
        self.stop_requested = True

    def finish(self) -> None:
        self.running = False

    def should_stop(self) -> bool:
        return self.stop_requested


execution_state = ExecutionState()


def stop_experiment() -> None:
    """Solicita a parada do experimento."""
    execution_state.stop()
