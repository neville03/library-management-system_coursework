
class _Logger:
    def __init__(self) -> None:
        self.clear()

    def empty(self) -> bool:
        return len(self._results) == 0

    def write(self, value: str = "") -> None:
        self._results.append(value)

    def write_all(self, values: list[str]) -> None:
        for value in values:
            self._results.append(value)

    def error(self, value: str = "") -> None:
        self.write(value)
        self.set_error()

    def error_all(self, values: list[str]) -> None:
        self.write_all(values)
        self.set_error()

    def set_error(self, ev: bool = True) -> None:
        self._errored = self._errored or ev

    def has_errored(self) -> bool:
        return self._errored

    def clear(self) -> None:
        self._results = []
        self._errored = False

    def print(self) -> str:
        return self.__str__()

    def flush(self) -> str:
        results = self.print()
        self.clear()

        return results

    def __str__(self) -> str:
        return "\n".join(self._results)

Logger = _Logger()
