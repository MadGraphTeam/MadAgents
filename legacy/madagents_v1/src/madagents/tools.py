import os
import subprocess
import threading
import time

from pathlib import Path
from typing import Tuple, Union, Optional, Dict, List, Literal, Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from madagents.cli_bridge.bridge_interface import CLISession, strip_control_codes

from madagents.utils import (
    pdf_to_content_block,
    image_to_content_block,
    pdf_to_anthropic_content_block,
    image_to_anthropic_content_block,
)

from madagents.bash_helpers import (
    SwitchableSink,
    RunningProcess,
    get_log_root,
    register_running_process,
    pump_stream_to_sink,
    get_last_lines_info,
    terminate_processes_for_current_logs,
    terminate_processes_for_log_root,
)

from madagents.patch_helpers import apply_patch_operation_to_fs

#########################################################################
## web_search ###########################################################
#########################################################################

web_search_tool = {"type": "web_search"}
anthropic_web_search_tool = {"type": "web_search_20250305", "name": "web_search"}

#########################################################################
## bash #################################################################
#########################################################################

def bash(commands: str) -> Tuple[str, dict]:
    """Run a bash command string and capture stdout/stderr with tailing."""
    timeout_s = 600
    virtual_venv = os.environ.get("VIRTUAL_ENV", None)
    env = os.environ.copy()
    if virtual_venv is not None:
        env["PATH"] = f"{virtual_venv}/bin:" + env.get("PATH", "")
    else:
        env["PATH"] = env.get("PATH", "")

    # Start a new process group so we can terminate descendants as needed.
    proc = subprocess.Popen(
        commands,
        env=env,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash",
        start_new_session=True,
        text=False,
        bufsize=0
    )

    base = str(proc.pid)
    out_sink = SwitchableSink(base=base, kind="stdout", max_bytes=40_000)
    err_sink = SwitchableSink(base=base, kind="stderr", max_bytes=40_000)

    stop_event = threading.Event()
    t_out = threading.Thread(target=pump_stream_to_sink, args=(proc.stdout, out_sink, stop_event), daemon=True)
    t_err = threading.Thread(target=pump_stream_to_sink, args=(proc.stderr, err_sink, stop_event), daemon=True)
    t_out.start()
    t_err.start()

    try:
        proc.wait(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True

    artefact = {
        "commands": commands,
        "pid": proc.pid,
        "timeout": timed_out,
        "exit_code": None if timed_out else proc.returncode,
    }

    stdout_text = ""
    stderr_text = ""

    # If timed out, force spill to file so we keep capturing output after returning.
    if timed_out:
        out_sink.attach_file()
        err_sink.attach_file()

        artefact["stdout_path"] = out_sink.path
        artefact["stderr_path"] = err_sink.path

        msg_lines = [
            f"Process still running after {timeout_s}s (pid={proc.pid}).",
            "Output is being written to files:",
            f"stdout: {out_sink.path}",
            f"stderr: {err_sink.path}",
        ]

        tail, n, truncated = get_last_lines_info(out_sink, n_lines=20)
        if truncated:
            artefact["stdout_last_n"] = n # we set this only if truncated
        stdout_text = tail or ""
        if tail:
            label = f"stdout (last {f'{n} lines' if n > 1 else 'line'}) so far" if truncated else "stdout so far"
            msg_lines.append(f"--- {label} ---")
            msg_lines.append(tail)

        tail, n, truncated = get_last_lines_info(err_sink, n_lines=20)
        if truncated:
            artefact["stderr_last_n"] = n # we set this only if truncated
        stderr_text = tail or ""
        if tail:
            label = f"stderr (last {f'{n} lines' if n > 1 else 'line'}) so far" if truncated else "stderr so far"
            msg_lines.append(f"--- {label} ---")
            msg_lines.append(tail)

        artefact["stdout"] = stdout_text
        artefact["stderr"] = stderr_text

        register_running_process(
            get_log_root(),
            RunningProcess(
                pid=proc.pid,
                proc=proc,
                t_out=t_out,
                t_err=t_err,
                out_sink=out_sink,
                err_sink=err_sink,
                stop_event=stop_event,
            ),
        )

        return "\n".join(msg_lines), artefact

    # Completed within timeout: wait for pumps to drain remaining data
    t_out.join()
    t_err.join()

    out_lines = [f"[exit code] {proc.returncode}"]

    # stdout reporting
    if out_sink.spilled and out_sink.path:
        artefact["stdout_path"] = out_sink.path
        tail, n, truncated = get_last_lines_info(out_sink, n_lines=20)
        if truncated:
            artefact["stdout_last_n"] = n # we set this only if truncated
        stdout_text = tail or ""
        out_lines.append(f"stdout was large; full stdout is in: {out_sink.path}")
        if tail:
            truncated_str = f" (last {f'{n} lines' if n > 1 else 'line'})" if truncated else ""
            out_lines.append(f"--- stdout{truncated_str} ---")
            out_lines.append(tail)
    else:
        stdout = out_sink.get_buffered().decode("utf-8", errors="replace")
        stdout_text = stdout
        if stdout:
            out_lines.append("--- stdout ---")
            out_lines.append(stdout)

    # stderr reporting
    if err_sink.spilled and err_sink.path:
        artefact["stderr_path"] = err_sink.path
        tail, n, truncated = get_last_lines_info(err_sink, n_lines=20)
        if truncated:
            artefact["stderr_last_n"] = n # we set this only if truncated
        stderr_text = tail or ""
        out_lines.append(f"stderr was large; full stderr is in: {err_sink.path}")
        if tail:
            truncated_str = f" (last {f'{n} lines' if n > 1 else 'line'})" if truncated else ""
            out_lines.append(f"--- stderr{truncated_str} ---")
            out_lines.append(tail)
    else:
        stderr = err_sink.get_buffered().decode("utf-8", errors="replace")
        stderr_text = stderr
        if stderr:
            out_lines.append("--- stderr ---")
            out_lines.append(stderr)

    artefact["stdout"] = stdout_text
    artefact["stderr"] = stderr_text

    return "\n".join(out_lines), artefact

class BashArgs(BaseModel):
    commands: str = Field(
        ...,
        description=(
            "Commands to be executed in bash. "
            "Provide commands as in a terminal — no leading \"$\", backticks, or markdown fences. "
            "Multi-line scripts are allowed."
        ),
        examples=["ls -la /output", "python3 script.py --input data.csv"],
    )

bash_tool = StructuredTool.from_function(
    name="bash",
    description=(
        "Execute a command string using /bin/bash (non-interactive). "
        "The configured Python virtual environment is on PATH if it exists. "
        "Stdin is disabled (EOF). "
        "Commands have a 600s response window; if exceeded, the process continues in the background — "
        "the return value contains the PID and output file paths. "
        "Large outputs (>40 KB) are spilled to log files; the last lines are returned inline."
    ),
    func=bash,
    args_schema=BashArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

#########################################################################
## wait ###############################################################
#########################################################################

def wait(minutes: float) -> str:
    """Sleep for the requested number of minutes."""
    time.sleep(minutes * 60.0)
    return f"Waited {minutes} minutes"

class WaitArgs(BaseModel):
    minutes: float = Field(
        ...,
        description=("Minutes to wait before returning."),
    )

wait_tool = StructuredTool.from_function(
    name="wait",
    description=(
        "Wait for a given number of minutes."
    ),
    func=wait,
    args_schema=WaitArgs,
    return_direct=False,
    response_format="content"
)


#########################################################################
## apply_patch ##########################################################
#########################################################################

class ApplyPatchOp(BaseModel):
    type: Literal["create_file", "update_file", "delete_file"] = Field(
        ...,
        description="Patch operation type: create_file, update_file, or delete_file.",
    )
    path: str = Field(
        ...,
        description="File path (relative to /workspace or absolute).",
    )
    diff: Optional[str] = Field(
        None,
        description=(
            "Diff string (required for create_file/update_file; omit for delete_file). "
            "For create_file: the raw file content exactly as it should appear in the file. "
            "For update_file: context lines (space prefix), deletions (\"-\"), additions (\"+\"). "
            "Use \"@@ <anchor line>\" to jump the search to after a matching line; bare \"@@\" separates sections. "
            "Use \"*** End of File\" after a section to anchor matching near the end of the file."
        ),
    )

class ApplyPatchArgs(BaseModel):
    operations: List[ApplyPatchOp] = Field(
        ...,
        description="List of patch operations to apply.",
        examples=[
            [{"type": "create_file", "path": "/workspace/demo.txt", "diff": "Hello\nWorld\n"}],
            [{"type": "update_file", "path": "/workspace/demo.txt", "diff": "@@\n Hello\n-World\n+Universe\n"}],
            [{"type": "update_file", "path": "/workspace/demo.txt", "diff": "@@ Header\n Title\n-Old\n+New\n"}],
            [{"type": "update_file", "path": "/workspace/demo.txt", "diff": "@@\n A\n-1\n+2\n@@\n Z\n-x\n+y\n"}],
            [{"type": "update_file", "path": "/workspace/demo.txt", "diff": "@@\n Tail\n-Old\n+New\n*** End of File"}],
            [{"type": "delete_file", "path": "/workspace/demo.txt"}],
        ],
    )

def apply_patch(operations: List[ApplyPatchOp]) -> Tuple[str, Dict[str, Any]]:
    """Apply a batch of patch operations to the filesystem."""
    root_dir = Path("/workspace")

    results: List[Dict[str, Any]] = []
    all_ok = True

    for op in operations:
        ok, log = apply_patch_operation_to_fs(
            root_dir=root_dir,
            operation=op.model_dump(),  # dict with type/path/diff
        )
        results.append(
            {
                "type": op.type,
                "path": op.path,
                "status": "completed" if ok else "failed",
                "output": log,
            }
        )
        all_ok = all_ok and ok

    status = "completed" if all_ok else "failed"
    message = f"apply_patch {status}: {len(results)} operation(s)"
    details_lines = []
    for item in results:
        op_type = item.get("type") or ""
        path = item.get("path") or ""
        op_status = item.get("status") or ""
        output = item.get("output") or ""
        details_lines.append(f"- {op_type} {path}: {op_status} - {output}")
    if details_lines:
        message = message + "\nResults:\n" + "\n".join(details_lines)
    return message, {
        "status": status,
        "results": results,
    }

apply_patch_tool = StructuredTool.from_function(
    name="apply_patch",
    description=(
        "Create, update, or delete files via patch operations. "
        "Not for binary files. File writes use UTF-8 encoding. "
        "Control characters are rejected in diff except \\n, \\t, and \\r. "
        "After calling, returns a status and logs for each operation."
    ),
    func=apply_patch,
    args_schema=ApplyPatchArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

#########################################################################
## read_pdf #############################################################
#########################################################################

def read_pdf(pdf_file_path: str) -> Tuple[Union[list[dict], str], str]:
    """Validate and load a PDF file as a content block."""
    if not pdf_file_path.endswith(".pdf"):
        error_msg = f"Error: The file {pdf_file_path} does not end with .pdf"
        return error_msg, error_msg
    if not os.path.exists(pdf_file_path):
        error_msg = f"Error: The file {pdf_file_path} was not found."
        return error_msg, error_msg
    msg = f"File {pdf_file_path} opened."
    return [pdf_to_content_block(pdf_file_path)], msg

class ReadPDFArgs(BaseModel):
    pdf_file_path: str = Field(..., description="Absolute path of the PDF file.")

openai_read_pdf_tool = StructuredTool.from_function(
    name="read_pdf",
    description=(
        "Makes the PDF content available in the conversation. "
        "Path must be absolute, must exist, and must end with .pdf. "
        "On failure, returns an error message."
    ),
    func=read_pdf,
    args_schema=ReadPDFArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

def read_pdf_anthropic(pdf_file_path: str) -> Tuple[Union[list[dict], str], str]:
    """Validate and load a PDF file as an Anthropic document content block."""
    if not pdf_file_path.endswith(".pdf"):
        error_msg = f"Error: The file {pdf_file_path} does not end with .pdf"
        return error_msg, error_msg
    if not os.path.exists(pdf_file_path):
        error_msg = f"Error: The file {pdf_file_path} was not found."
        return error_msg, error_msg
    msg = f"File {pdf_file_path} opened."
    return [pdf_to_anthropic_content_block(pdf_file_path)], msg

anthropic_read_pdf_tool = StructuredTool.from_function(
    name="read_pdf",
    description=(
        "Makes the PDF content available in the conversation. "
        "Path must be absolute, must exist, and must end with .pdf. "
        "On failure, returns an error message."
    ),
    func=read_pdf_anthropic,
    args_schema=ReadPDFArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

#########################################################################
## read_image ###########################################################
#########################################################################

def read_image(image_file_path: str) -> Tuple[Union[list[dict], str], str]:
    """Validate and load an image file as a content block."""
    valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    if not image_file_path.lower().endswith(valid_exts):
        error_msg = f"Error: The file {image_file_path} does not end with one of {', '.join(valid_exts)}"
        return error_msg, error_msg
    if not os.path.exists(image_file_path):
        error_msg = f"Error: The file {image_file_path} was not found."
        return error_msg, error_msg
    msg = f"File {image_file_path} opened."
    return [image_to_content_block(image_file_path)], msg

class ReadImageArgs(BaseModel):
    image_file_path: str = Field(..., description="Absolute path of the image file.")

openai_read_image_tool = StructuredTool.from_function(
    name="read_image",
    description=(
        "Makes the image available in the conversation. "
        "Supported extensions: .png, .jpg, .jpeg, .webp, .gif. "
        "Path must be absolute and must exist. "
        "On failure, returns an error message."
    ),
    func=read_image,
    args_schema=ReadImageArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

def read_image_anthropic(image_file_path: str) -> Tuple[Union[list[dict], str], str]:
    """Validate and load an image file as an Anthropic image content block."""
    valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    if not image_file_path.lower().endswith(valid_exts):
        error_msg = f"Error: The file {image_file_path} does not end with one of {', '.join(valid_exts)}"
        return error_msg, error_msg
    if not os.path.exists(image_file_path):
        error_msg = f"Error: The file {image_file_path} was not found."
        return error_msg, error_msg
    msg = f"File {image_file_path} opened."
    return [image_to_anthropic_content_block(image_file_path)], msg

anthropic_read_image_tool = StructuredTool.from_function(
    name="read_image",
    description=(
        "Makes the image available in the conversation. "
        "Supported extensions: .png, .jpg, .jpeg, .webp, .gif. "
        "Path must be absolute and must exist. "
        "On failure, returns an error message."
    ),
    func=read_image_anthropic,
    args_schema=ReadImageArgs,
    return_direct=False,
    response_format="content_and_artifact"
)

#########################################################################
## int_cli time settings ################################################
#########################################################################

WAIT_S_DEFAULT = 2.0
TIMEOUT_SECONDS = 10. * 60.
IDLE_TIMEOUT_DEFAULT = 2.0

#########################################################################
## get_int_cli_status ###################################################
#########################################################################

def _count_lines(data: bytes) -> int:
    """Count lines in a byte string, accounting for missing trailing newline."""
    if not data:
        return 0
    count = data.count(b"\n")
    if not data.endswith(b"\n"):
        count += 1
    return count

def get_int_cli_status(session: CLISession):
    """Return a tool function that reports interactive CLI session status."""
    def int_cli_status() -> Tuple[str, dict]:
        """Summarize transcript position, context, and new output."""
        first_seen = not getattr(session, "_int_cli_status_seen", False)
        session._int_cli_status_seen = True
        status = "Potentially unseen CLI session" if first_seen else "Ongoing CLI session"

        transcript_path = None
        if session.handle is not None:
            transcript_path = session.handle.transcript_host
        elif session.dir:
            transcript_path = os.path.join(session.dir, "pure_transcript.log")

        data = b""
        if transcript_path and os.path.exists(transcript_path):
            with open(transcript_path, "rb") as f:
                data = f.read()

        file_len = len(data)
        previous_offset = min(max(session.read_offset, 0), file_len)
        new_bytes = data[previous_offset:file_len] if file_len > previous_offset else b""
        session.read_offset = file_len
        prefix = data[:session.read_offset]
        new_output = strip_control_codes(new_bytes.decode("utf-8", errors="replace"))

        total_lines = _count_lines(data)
        lines_before = _count_lines(prefix)
        lines_after = max(total_lines - lines_before, 0)
        read_position_line = lines_before

        context_lines = prefix.splitlines()[-10:] if prefix else []
        context_text = ""
        context_start = None
        if context_lines:
            context_start = max(1, read_position_line - len(context_lines) + 1)
            rendered = []
            for line in context_lines:
                text = strip_control_codes(line.decode("utf-8", errors="replace")).rstrip("\r")
                rendered.append(text)
            context_text = "\n".join(rendered)

        msg_lines = [
            f"{status} ({lines_before} lines before read position, {lines_after} lines after read position)"
        ]
        if context_text:
            msg_lines.append(f"--- context lines {context_start}-{read_position_line} ---")
            msg_lines.append(context_text)
        msg_lines.append("--- new cli output ---")
        if new_output:
            msg_lines.append(new_output)

        return "\n".join(msg_lines), {
            "status": status,
            "lines_before": lines_before,
            "lines_after": lines_after,
            "context_start": context_start,
            "context": context_text,
            "new_output": new_output
        }
    return int_cli_status

class IntCLIStatusArgs(BaseModel):
    pass

def get_int_cli_status_tool(session: CLISession):
    """Create a StructuredTool for interactive CLI status."""
    int_cli_status_tool = StructuredTool.from_function(
        name="int_cli_status",
        description=(
            "Summarize the interactive CLI session state and read any new output. "
            "Reports how many lines exist before/after the current read position, shows the last 10 lines before it and the new output after it."
        ),
        func=get_int_cli_status(session),
        args_schema=IntCLIStatusArgs,
        return_direct=False,
        response_format="content_and_artifact"
    )
    return int_cli_status_tool


#########################################################################
## read_int_cli_transcript ##############################################
#########################################################################

def get_read_int_cli_transcript(session: CLISession):
    """Return a tool function to read transcript lines from the CLI session."""
    def read_int_cli_transcript(start_line: int, end_line: int) -> Tuple[str, dict]:
        """Read and format transcript lines, advancing the read offset."""
        text, start_line, end_line = session.read_transcript_lines(
            start_line=start_line,
            end_line=end_line,
            advance_read_offset=True,
        )
        if start_line == 0 and end_line == 0:
            error_msg = "Error: CLI transcript not found."
            return error_msg, {
                "text": "",
                "start_line": 0,
                "end_line": 0,
                "error": error_msg,
            }

        llm_message = f"--- cli transcript {start_line}-{end_line} ---\n{text}"
        return llm_message, {
            "text": text,
            "start_line": start_line,
            "end_line": end_line,
        }
    return read_int_cli_transcript

class ReadIntCLITranscriptArgs(BaseModel):
    start_line: int = Field(..., description="First line number to return (1-based).")
    end_line: int = Field(..., description="Last line number to return (inclusive). Use -1 for last line.")

def get_read_int_cli_transcript_tool(session: CLISession):
    """Create a StructuredTool for reading CLI transcript lines."""
    read_int_cli_transcript_tool = StructuredTool.from_function(
        name="read_int_cli_transcript",
        description=(
            "Read lines from the interactive CLI transcript. "
            "end_line is processed first: -1 means last line; otherwise it is clamped. "
            "start_line is then clamped to [1, end_line]. "
            "If end_line is beyond the current read position, the read_offset is advanced."
        ),
        func=get_read_int_cli_transcript(session),
        args_schema=ReadIntCLITranscriptArgs,
        return_direct=False,
        response_format="content_and_artifact"
    )
    return read_int_cli_transcript_tool


#########################################################################
## read_int_cli_output ##################################################
#########################################################################

def get_read_int_cli_output(session: CLISession):
    """Return a tool function to read new CLI output."""
    def read_int_cli_output(wait_s: float = WAIT_S_DEFAULT) -> Tuple[str, str]:
        """Read new CLI output and return formatted text plus raw output."""
        cli_output = session.read_output(
            wait_s=wait_s,
            timeout_s=TIMEOUT_SECONDS,
            idle_grace_s=IDLE_TIMEOUT_DEFAULT,
        )
        llm_message = "--- cli output ---\n" + cli_output
        return llm_message, cli_output
    return read_int_cli_output

class ReadIntCLIOutputArgs(BaseModel):
    wait_s: float = Field(
        WAIT_S_DEFAULT,
        description=(
            "Seconds to wait before reading any CLI output. Output is read only after this delay. "
            f"Default {WAIT_S_DEFAULT:g} s. "
            "Negative values are clipped to 0.\n"
            "During installations and generations/simulations, prefer using 60-600 s."
        ),
    )

def get_read_int_cli_output_tool(session: CLISession):
    """Create a StructuredTool for reading CLI output."""
    read_int_cli_output_tool = StructuredTool.from_function(
        name="read_int_cli_output",
        description=(
            "Collect new output from the already-running interactive CLI session. "
            "Use this when you have received a new message from the user or you expect a previous command to still be printing output "
            "(e.g. when a previous 'run_cli_command' call indicated that more output may follow)."
        ),
        func=get_read_int_cli_output(session),
        args_schema=ReadIntCLIOutputArgs,
        return_direct=False,
        response_format="content_and_artifact"
    )
    return read_int_cli_output_tool


#########################################################################
## run_int_cli_command ##################################################
#########################################################################

def get_run_int_cli_command(session: CLISession):
    """Return a tool function to execute a CLI command."""
    def run_int_cli_command(command: str, wait_s: float = WAIT_S_DEFAULT) -> Tuple[str, str]:
        """Run a command in the CLI session and return formatted output."""
        cli_output = session.run_command(
            command,
            wait_s=wait_s,
            timeout_s=TIMEOUT_SECONDS,
            idle_grace_s=IDLE_TIMEOUT_DEFAULT,
        )

        llm_message = "--- cli output ---\n" + cli_output
        return llm_message, cli_output
    return run_int_cli_command

class RunIntCLICommandArgs(BaseModel):
    command: str = Field(..., description="A command to execute in the interactive CLI session.")
    wait_s: float = Field(
        WAIT_S_DEFAULT,
        description=(
            "Seconds to wait before reading any CLI output. Output is read only after this delay. "
            f"Default {WAIT_S_DEFAULT:g} s. "
            "Negative values are clipped to 0.\n"
            "During installations and generations/simulations, prefer using 60-600 s."
        ),
    )

def get_run_int_cli_command_tool(session: CLISession):
    """Create a StructuredTool for running CLI commands."""
    run_int_cli_command_tool = StructuredTool.from_function(
        name="run_int_cli_command",
        description="Execute a single, deterministic CLI command in the already-running interactive CLI session and return its output.",
        func=get_run_int_cli_command(session),
        args_schema=RunIntCLICommandArgs,
        return_direct=False,
        response_format="content_and_artifact"
    )
    return run_int_cli_command_tool


#########################################################################
## save_answer ##########################################################
#########################################################################

def save_answer(file_path: str, content: str) -> str:
    """Write text content to an absolute path, overwriting if needed."""
    if not os.path.isabs(file_path):
        return f"Error: The file path {file_path} is not absolute."
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.isdir(dir_path):
        return f"Error: The directory {dir_path} does not exist."
    try:
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(content)
    except OSError as exc:
        return f"Error: Could not write to {file_path}: {exc}"
    return f"Saved answer to {file_path}."

class SaveAnswerArgs(BaseModel):
    file_path: str = Field(..., description="Absolute path of the file to write.")
    content: str = Field(..., description="Text content to save to the file.")

save_answer_tool = StructuredTool.from_function(
    name="save_answer",
    description="Save a text answer to a file, overwriting the file if it already exists.",
    func=save_answer,
    args_schema=SaveAnswerArgs,
    return_direct=False,
)


