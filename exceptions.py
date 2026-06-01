class LogtraceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"logtrace: {status_code} - {message}")
        self.status_code = s
