from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


@dataclass
class AccessibleProgress:
    output: Callable[[str], None] = print
    enabled: bool = True
    percent_step: int = 10
    heartbeat_seconds: int = 15

    def __post_init__(self) -> None:
        self._started_at = time.monotonic()
        self._phase_started_at = self._started_at
        self._last_bucket = -1

    def say(self, text: str) -> None:
        if self.enabled:
            self.output(text)

    def phase(self, current: int, total: int, label: str) -> None:
        self._phase_started_at = time.monotonic()
        self._last_bucket = -1
        self.say(f"Operação {current} de {total}: {label}.")

    def progress(
        self,
        label: str,
        fraction: float,
        *,
        completed_bytes: int | None = None,
        total_bytes: int | None = None,
    ) -> None:
        percent = max(0, min(100, int(fraction * 100)))
        bucket = 100 if percent >= 100 else (percent // self.percent_step) * self.percent_step
        if bucket <= self._last_bucket:
            return
        self._last_bucket = bucket

        size_text = ""
        if completed_bytes is not None and total_bytes:
            size_text = (
                f" {completed_bytes / 1048576:.1f} MB de "
                f"{total_bytes / 1048576:.1f} MB."
            )
        elapsed = format_duration(time.monotonic() - self._phase_started_at)
        self.say(
            f"{label}: {bucket} por cento.{size_text} "
            f"Tempo decorrido: {elapsed}."
        )

    def done(self, label: str) -> None:
        elapsed = format_duration(time.monotonic() - self._phase_started_at)
        self.say(f"{label} concluído. Tempo: {elapsed}.")

    def summary(self, label: str = "Processo remoto") -> None:
        elapsed = format_duration(time.monotonic() - self._started_at)
        self.say(f"{label} concluído em {elapsed}.")

    @contextmanager
    def waiting(self, label: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return

        started = time.monotonic()
        stopped = threading.Event()

        def heartbeat() -> None:
            while not stopped.wait(self.heartbeat_seconds):
                elapsed = format_duration(time.monotonic() - started)
                self.say(f"{label} continua em andamento. Tempo: {elapsed}.")

        self.say(f"{label} iniciado.")
        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            yield
        finally:
            stopped.set()
            thread.join(timeout=0.2)
            elapsed = format_duration(time.monotonic() - started)
            self.say(f"{label} concluído. Tempo: {elapsed}.")
