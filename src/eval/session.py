"""Shared session protocol and concrete implementations for eval harnesses.

All eval harnesses (answer, generate, verify) use the same
:class:`QuerySession` protocol.  Implementations SHOULD maintain
conversation context across successive ``ask()`` calls so that retry
loops can reference prior turns (e.g. the agent sees its previous
attempt and the error feedback).

If a fresh conversation is needed (e.g. a new question), create a
new session instance — the factory pattern used by
``run_evaluation`` already does this.

Two concrete implementations are provided:

- :class:`ClaudeCodeSession` — bare Claude Code via the ``claude`` CLI.
  Prepares a minimal ``.claude/`` directory (settings only).
- :class:`MadAgentsSession` — full MadAgents orchestrator setup.
  Prepares ``.claude/`` with CLAUDE.md, agent cards, settings, and
  appends the orchestrator system prompt.

Both sessions prepare their ``.claude/`` directory at ``cwd`` during
``__init__``, so they can coexist in the same container by using
different working directories.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from eval.utils.errors import TransientError, detect_transient_error

# Add claude_code/scripts to path for build_claude_dir import.
# parents[2] = repo root on host (.../AgentFitterDev), / in container.
import sys as _sys
_CLAUDE_CODE_DIR = Path(__file__).resolve().parents[2] / "claude_code"
if not (_CLAUDE_CODE_DIR / "scripts").is_dir():
    # In-container fallback: /src/claude_code/scripts
    _CLAUDE_CODE_DIR = Path(__file__).resolve().parents[1] / "claude_code"
_sys.path.insert(0, str(_CLAUDE_CODE_DIR))
from scripts.build_claude_dir import build_claude_dir as _build_claude_dir


@runtime_checkable
class QuerySession(Protocol):
    """Async interface for querying an agent.

    Implementations SHOULD maintain conversation context across
    successive ``ask()`` calls — each call appends to the conversation
    history, so the agent sees prior turns.

    The agent's system prompt, model, container setup, and credentials
    are internal to the implementation — the harness only sends user
    prompts.
    """

    async def ask(self, user_prompt: str) -> str: ...


# ═══════════════════════════════════════════════════════════════════════
#  Base CLI session
# ═══════════════════════════════════════════════════════════════════════

def _find_claude_bin() -> str:
    """Locate the claude binary.

    Checks (in order):
    1. ``claude`` on PATH
    2. ``/opt/claude/versions/<version>`` — inside containers, the host
       Claude install is bind-mounted here with a versioned filename
    3. Common host install locations
    """
    found = shutil.which("claude")
    if found:
        return found

    # Inside containers: host install bind-mounted at /opt/claude/.
    versions_dir = Path("/opt/claude/versions")
    if versions_dir.is_dir():
        # Pick the newest version (reverse-sorted by name).
        for candidate in sorted(versions_dir.iterdir(), reverse=True):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)

    for candidate in [
        Path.home() / ".local" / "bin" / "claude",
        Path("/usr/local/bin/claude"),
    ]:
        if candidate.exists():
            return str(candidate)
    return "claude"


class _BaseCLISession:
    """Shared CLI subprocess logic for concrete sessions.

    On construction, prepares the ``.claude/`` directory at *cwd* via
    :meth:`_setup_workdir`.  Subclasses extend this to add CLAUDE.md,
    agent cards, etc.
    """

    def __init__(
        self,
        *,
        cwd: str | Path,
        name: str = "",
        system_prompt: str = "",
        model: str | None = None,
        permission_mode: str | None = "bypassPermissions",
        cli_path: str | Path | None = None,
        setting_sources: list[str] | None = None,
        max_turns: int | None = None,
        env: dict[str, str] | None = None,
        disallowed_tools: list[str] | None = None,
        transcript: list[dict[str, Any]] | None = None,
        log_dir: str | Path | None = None,
        container: "ContainerConfig | None" = None,
    ):
        self._cwd = str(cwd)
        self._name = name
        self._system_prompt = system_prompt
        self._model = model
        self._permission_mode = permission_mode
        self._cli_path = str(cli_path) if cli_path else _find_claude_bin()
        self._setting_sources = setting_sources
        self._max_turns = max_turns
        self._env = env
        self._disallowed_tools = disallowed_tools
        self._container = container
        self._session_id: str | None = None
        self._transcript: list[dict[str, Any]] = transcript if transcript is not None else []
        self._messages: list[str] = []  # all user-facing text blocks
        self._log_dir = Path(log_dir) if log_dir else None
        self._ask_count = 0

        self._setup_workdir()

    def _setup_workdir(self) -> None:
        """Prepare ``.claude/`` at the working directory.

        Uses :func:`build_claude_dir` for consistent setup across all
        consumers (interactive, pipeline, examples).
        """
        workdir = Path(self._cwd)
        workdir.mkdir(parents=True, exist_ok=True)
        _build_claude_dir(workdir / ".claude", session_type="bare")

    def _log(self, stream: str, text: str) -> None:
        """Append text to a log file (e.g. ``answerer_stdout.log``)."""
        if self._log_dir is None or not text:
            return
        self._log_dir.mkdir(parents=True, exist_ok=True)
        name = self._name or "session"
        path = self._log_dir / f"{name}_{stream}.log"
        with open(path, "a") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")

    def map_path(self, host_path: str | Path) -> str:
        """Map a host path to a container path (if container is configured).

        Use this when building prompts that reference file paths the LLM
        will read/write.  Returns the path unchanged if no container.
        """
        if self._container:
            return self._container.host_to_container(host_path)
        return str(host_path)

    @property
    def name(self) -> str:
        return self._name

    @property
    def transcript(self) -> list[dict[str, Any]]:
        """Accumulated transcript as a list of dicts (all ``ask()`` calls)."""
        return self._transcript

    @property
    def messages(self) -> list[str]:
        """All user-facing text messages across all ``ask()`` calls."""
        return self._messages

    def _build_cmd(self, user_prompt: str) -> list[str]:
        """Build the CLI command.  Subclasses may extend."""
        cmd = [self._cli_path, "-p", user_prompt, "--output-format", "stream-json", "--verbose"]

        if self._system_prompt:
            cmd += ["--append-system-prompt", self._system_prompt]
        if self._model:
            cmd += ["--model", self._model]
        if self._permission_mode:
            cmd += ["--permission-mode", self._permission_mode]
        if self._disallowed_tools:
            cmd += ["--disallowed-tools", ",".join(self._disallowed_tools)]
        if self._max_turns is not None:
            cmd += ["--max-turns", str(self._max_turns)]
        if self._setting_sources:
            cmd += ["--setting-sources", ",".join(self._setting_sources)]

        # Session resume for multi-turn.
        if self._session_id:
            cmd += ["--resume", self._session_id]

        return cmd

    async def ask(self, user_prompt: str) -> str:
        """Send a prompt and return the response text.

        Maintains conversation context via CLI ``--resume`` parameter.
        All stream-json events are appended to :attr:`transcript`.
        Raises :class:`TransientError` on auth/rate-limit failures.
        """
        cmd = self._build_cmd(user_prompt)

        # Wrap in container if configured.
        if self._container:
            cmd = self._container.wrap_command(cmd)

        call_idx = self._ask_count
        self._ask_count += 1

        # Build clean environment (filter out CLAUDECODE to avoid nesting issues).
        env = self._env if self._env else {
            k: v for k, v in os.environ.items() if k != "CLAUDECODE"
        }
        # Disable auto-memory for eval sessions.
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"

        # Record the user prompt in the transcript.
        self._transcript.append({
            "type": "user", "session": self._name, "prompt": user_prompt,
        })

        result_text = ""
        is_error = False
        proc = None
        non_json_lines: list[str] = []
        all_stdout_lines: list[str] = []

        stderr_text = ""

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None if self._container else self._cwd,
                env=env,
                limit=10 * 1024 * 1024,  # 10 MB line buffer (default 64 KB is too small)
            )

            assert proc.stdout is not None
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                all_stdout_lines.append(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    non_json_lines.append(line)
                    continue

                # Record in transcript.
                event_copy = dict(event)
                event_copy["session"] = self._name
                self._transcript.append(event_copy)

                event_type = event.get("type", "")

                if event_type == "rate_limit_event":
                    info = event.get("rate_limit_info", {})
                    if info.get("status") == "rejected":
                        proc.kill()
                        raise TransientError(
                            f"Rate limit rejected: resets_at={info.get('resetsAt')}"
                        )

                elif event_type == "assistant":
                    error = event.get("error")
                    if error:
                        match = detect_transient_error(str(error))
                        if match:
                            proc.kill()
                            raise TransientError(
                                f"Transient error from CLI: {match}"
                            )

                    # Collect user-facing text blocks.
                    msg = event.get("message", {})
                    for block in msg.get("content", []):
                        if block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text:
                                self._messages.append(text)

                elif event_type == "result":
                    result_text = event.get("result", "")
                    is_error = event.get("is_error", False)
                    self._session_id = event.get("session_id")

            await proc.wait()

            # Check stderr.
            assert proc.stderr is not None
            stderr_data = await proc.stderr.read()
            if stderr_data:
                stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    match = detect_transient_error(stderr_text)
                    if match:
                        raise TransientError(f"Transient error (stderr): {match}")

            # Log any non-JSON stdout lines (often error messages).
            if non_json_lines:
                print(f"  [stdout] {' | '.join(non_json_lines[:5])}")

            # Handle non-zero exit with no result.
            if proc.returncode and proc.returncode != 0 and not result_text:
                error_detail = stderr_text or " | ".join(non_json_lines[:3]) or "unknown error"
                raise RuntimeError(
                    f"claude exited with code {proc.returncode}: {error_detail[:500]}"
                )

            # Log stderr if present (even on success).
            if stderr_text:
                print(f"  [stderr] {stderr_text[:500]}")

        except TransientError:
            raise
        except asyncio.CancelledError:
            if proc and proc.returncode is None:
                proc.kill()
            raise
        except Exception as e:
            match = detect_transient_error(str(e))
            if match:
                raise TransientError(f"Transient error: {match}") from e
            raise
        finally:
            # Always save logs, even on error.
            separator = f"\n{'=' * 40} ask #{call_idx} {'=' * 40}\n"
            self._log("cmd", separator + " ".join(cmd))
            self._log("stdout", separator + "\n".join(all_stdout_lines))
            if stderr_text:
                self._log("stderr", separator + stderr_text)
            if proc and proc.returncode is not None:
                self._log("exit", separator + str(proc.returncode))

        if is_error:
            match = detect_transient_error(result_text)
            if match:
                raise TransientError(f"Transient error: {match}")
            print(f"  WARNING: Agent returned error: {result_text[:200]}")

        return result_text


# ═══════════════════════════════════════════════════════════════════════
#  Claude Code session (bare)
# ═══════════════════════════════════════════════════════════════════════

class ClaudeCodeSession(_BaseCLISession):
    """Bare Claude Code session via the ``claude`` CLI.

    No agent definitions — just a single Claude Code instance with a
    configurable system prompt.  Used for question generation, grading,
    verification, and other tasks that don't need the multi-agent setup.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════
#  MadAgents session
# ═══════════════════════════════════════════════════════════════════════

class MadAgentsSession(_BaseCLISession):
    """Full MadAgents orchestrator session.

    Extends the base session with the complete MadAgents setup:

    - ``.claude/CLAUDE.md`` — operational guidelines
    - ``.claude/agents/*.md`` — agent cards
    - ``--append-system-prompt`` — orchestrator role and delegation rules
    All assets are read from ``src/claude_code/`` and copied into the
    session's working directory during ``__init__``.  If *system_prompt*
    is not provided, the default orchestrator prompt is loaded from
    ``src/claude_code/prompts/system-prompt-append.md``.
    """

    def __init__(
        self,
        *,
        cwd: str | Path,
        name: str = "",
        system_prompt: str = "",
        model: str | None = None,
        permission_mode: str | None = "bypassPermissions",
        cli_path: str | Path | None = None,
        setting_sources: list[str] | None = None,
        max_turns: int | None = None,
        env: dict[str, str] | None = None,
        disallowed_tools: list[str] | None = None,
        transcript: list[dict[str, Any]] | None = None,
        log_dir: str | Path | None = None,
        container: "ContainerConfig | None" = None,
    ):
        # Default system prompt: orchestrator role from prompts/.
        if not system_prompt:
            prompt_path = _CLAUDE_CODE_DIR / "prompts" / "system-prompt-append.md"
            if prompt_path.exists():
                system_prompt = prompt_path.read_text()

        super().__init__(
            cwd=cwd,
            name=name,
            system_prompt=system_prompt,
            model=model,
            permission_mode=permission_mode,
            cli_path=cli_path,
            setting_sources=setting_sources,
            max_turns=max_turns,
            env=env,
            disallowed_tools=disallowed_tools,
            transcript=transcript,
            log_dir=log_dir,
            container=container,
        )

    def _setup_workdir(self) -> None:
        """Prepare full MadAgents ``.claude/`` layout.

        Uses :func:`build_claude_dir` with ``session_type="madagents"``.
        Doc editing is disabled in the eval pipeline (no MCP server).
        """
        workdir = Path(self._cwd)
        workdir.mkdir(parents=True, exist_ok=True)
        _build_claude_dir(
            workdir / ".claude",
            session_type="madagents",
            doc_editing=False,
        )

