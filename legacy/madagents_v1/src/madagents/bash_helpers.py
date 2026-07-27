import os
import signal
import subprocess
import threading

from collections import deque

from dataclasses import dataclass, field
from typing import Optional, Dict, List


class SwitchableSink:
    """Buffer output in memory until it exceeds a threshold, then spill to disk."""
    def __init__(self, base: str, kind: str, max_bytes: int = 2_000_000):
        """Initialize the sink with an in-memory buffer and spill settings."""
        self.base = base
        self.kind = kind  # "stdout" or "stderr"
        self.max_bytes = max_bytes

        self._buf = deque()
        self._buf_bytes = 0
        self._lock = threading.Lock()

        self._f = None
        self.path = None
        self.spilled = False

    def _spill_locked(self):
        """Move buffered output to a file (caller must hold lock)."""
        # Caller holds lock
        if self._f is not None:
            return

        self.path = _reserve_nonexistent_path(self.base, self.kind)
        f = open(self.path, "ab", buffering=0)

        # YES: flush buffered output into the file
        while self._buf:
            f.write(self._buf.popleft())
        self._buf_bytes = 0

        self._f = f
        self.spilled = True

    def attach_file(self):
        """Force output to be spilled to a file."""
        with self._lock:
            self._spill_locked()

    def write(self, chunk: bytes):
        """Append bytes to the buffer or spill file if the buffer is too large."""
        if not chunk:
            return
        with self._lock:
            if self._f is not None:
                self._f.write(chunk)
                return

            if self._buf_bytes + len(chunk) > self.max_bytes:
                self._spill_locked()
                self._f.write(chunk)
                return

            self._buf.append(chunk)
            self._buf_bytes += len(chunk)

    def get_buffered(self) -> bytes:
        """Return the buffered output when still in-memory."""
        with self._lock:
            if self._f is not None:
                return b""
            return b"".join(self._buf)

    def close(self):
        """Close any underlying file handle, ignoring errors."""
        with self._lock:
            if self._f is not None:
                try:
                    self._f.close()
                except Exception:
                    pass
                self._f = None

@dataclass
class RunningProcess:
    pid: int
    proc: subprocess.Popen
    t_out: threading.Thread
    t_err: threading.Thread
    out_sink: SwitchableSink
    err_sink: SwitchableSink
    stop_event: threading.Event

_RUNNING_PROCESSES: Dict[str, Dict[int, RunningProcess]] = {}
_RUNNING_PROCESSES_LOCK = threading.Lock()

def get_log_root() -> str:
    """Return the root directory used for log discovery."""
    return os.path.realpath("/logs")

def register_running_process(log_root: str, record: RunningProcess) -> None:
    """Track a running process by log root and PID."""
    with _RUNNING_PROCESSES_LOCK:
        by_pid = _RUNNING_PROCESSES.setdefault(log_root, {})
        by_pid[record.pid] = record

def _pop_running_processes(log_root: str) -> List[RunningProcess]:
    """Remove and return all tracked processes for a log root."""
    with _RUNNING_PROCESSES_LOCK:
        by_pid = _RUNNING_PROCESSES.pop(log_root, {})
        return list(by_pid.values())

def pump_stream_to_sink(stream, sink: SwitchableSink, stop_event: Optional[threading.Event] = None, chunk_size: int = 8192):
    """Continuously read a stream into a sink until EOF or stop."""
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            if stop_event is not None and stop_event.is_set():
                break
            sink.write(chunk)
    except Exception:
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass
        sink.close()

def _reserve_nonexistent_path(base: str, kind: str, max_tries: int = 1_000) -> str:
    """Reserve a unique log path for a given base/kind."""
    log_dir = "/logs/tool_output"
    os.makedirs(log_dir, exist_ok=True)

    for i in range(max_tries):
        suffix = "" if i == 0 else f".{i}"
        path = os.path.join(log_dir, f"{base}{suffix}.{kind}.log")
        try:
            # reserve+create the file atomically
            with open(path, "xb"):
                pass
            return path
        except FileExistsError:
            continue

    raise RuntimeError(f"Could not reserve free log filename in {log_dir} after {max_tries} tries.")

def _tail_last_lines_from_bytes_info(data: bytes, n_lines: int = 20) -> tuple[str, int, bool]:
    """Return a UTF-8 tail string, line count, and truncation flag."""
    if not data:
        return "", 0, False
    lines = data.splitlines()
    total = len(lines)
    tail_lines = lines[-n_lines:] if total > n_lines else lines
    tail = b"\n".join(tail_lines).decode("utf-8", errors="replace")
    truncated = total > n_lines
    return tail, len(tail_lines), truncated

def _tail_last_lines_from_file_info(path: str, n_lines: int = 20, max_read_bytes: int = 512_000) -> tuple[str, int, bool]:
    """Tail the last lines from a file with bounded I/O."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            if end == 0:
                return "", 0, False
            to_read = min(end, max_read_bytes)
            f.seek(end - to_read, os.SEEK_SET)
            data = f.read(to_read)

        # IMPORTANT: with limited reads we may not know total lines in the whole file.
        # But we *can* know if truncation is very likely by checking whether we had
        # to read a partial file chunk.
        lines = data.splitlines()
        tail_lines = lines[-n_lines:] if len(lines) > n_lines else lines
        tail = b"\n".join(tail_lines).decode("utf-8", errors="replace")

        # If we didn't read the whole file, we can't be certain, but it's safe to say "last 20 lines"
        # when we return exactly n_lines AND we didn't read the entire file.
        read_was_partial = to_read < end
        truncated = (len(lines) > n_lines) or (read_was_partial and len(tail_lines) == n_lines)

        return tail, len(tail_lines), truncated
    except FileNotFoundError:
        return "", 0, False
    except Exception as e:
        return f"[tail error] {type(e).__name__}: {e}", 0, False

def get_last_lines_info(sink: SwitchableSink, n_lines: int = 20) -> tuple[str, int, bool]:
    """Return tail information from a sink, reading file or buffer."""
    if sink.spilled and sink.path:
        return _tail_last_lines_from_file_info(sink.path, n_lines=n_lines)
    return _tail_last_lines_from_bytes_info(sink.get_buffered(), n_lines=n_lines)

def terminate_processes_for_log_root(log_root: str, term_timeout_s: float = 5.0, kill_timeout_s: float = 2.0) -> int:
    """Terminate all tracked processes for a given log root."""
    records = _pop_running_processes(log_root)
    for record in records:
        proc = record.proc
        record.stop_event.set()
        try:
            pgid = os.getpgid(record.pid)
        except ProcessLookupError:
            pgid = None

        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        if proc.poll() is None:
            try:
                proc.wait(timeout=term_timeout_s)
            except subprocess.TimeoutExpired:
                if pgid is not None:
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                try:
                    proc.wait(timeout=kill_timeout_s)
                except subprocess.TimeoutExpired:
                    proc.wait()

        for stream in (proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass

        record.t_out.join()
        record.t_err.join()
        record.out_sink.close()
        record.err_sink.close()

    return len(records)

def terminate_processes_for_current_logs(term_timeout_s: float = 5.0, kill_timeout_s: float = 2.0) -> int:
    """Terminate all tracked processes under the default log root."""
    return terminate_processes_for_log_root(
        get_log_root(),
        term_timeout_s=term_timeout_s,
        kill_timeout_s=kill_timeout_s,
    )
