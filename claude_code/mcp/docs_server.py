#!/usr/bin/env python3
"""MCP server for editing MadGraph documentation.

Provides tools for doc editing and eval isolation:
- get_doc_draft: Copies docs to a specified path (must be under /workspace or /output)
- apply_doc_changes: Reads edited docs from a path, diffs, replaces real docs
- hide_paths: Moves paths to a vault outside bind mounts (invisible in container)
- show_paths: Restores hidden paths from the vault
- recover_vault: Lists/recovers vaults from crashed sessions
- get_transcript: Extracts and cleans a subagent's conversation transcript

Runs on the host. Files are shared via bind mounts.

Environment variables:
    DOCS_DIR: Host path to the MadGraph docs directory
    OVERVIEW_FILE: Host path to madgraph.md overview
    AGENT_HEADER: Host path to madgraph-operator header
    PATH_MAP: JSON mapping container prefixes to host paths
              e.g. {"/workspace": "/host/path/workspace", "/output": "/host/path/output"}
    CLAUDE_CONFIG_DIR: Host path to the Claude Code config directory (~/.config/.claude)
    SESSION_ID: Current Claude Code session UUID
    MCP_PORT: Port to listen on (default: 8089)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

DOCS_DIR = Path(os.environ.get(
    "DOCS_DIR",
    "src/madagents/software_instructions/madgraph",
)).resolve()
OVERVIEW_FILE = Path(os.environ.get(
    "OVERVIEW_FILE",
    "src/madagents/software_instructions/madgraph.md",
)).resolve()
AGENT_HEADER = Path(os.environ.get(
    "AGENT_HEADER",
    "claude_code/prompts/madgraph-operator.header.md",
)).resolve()

# Container-to-host path mapping.
_PATH_MAP_RAW = os.environ.get("PATH_MAP", "{}")
PATH_MAP: dict[str, str] = json.loads(_PATH_MAP_RAW)

# Allowed container prefixes for writing.
ALLOWED_PREFIXES = ["/workspace", "/output"]

AGENT_CARDS = [
    Path("claude_code/.claude/agents/madgraph-operator.md").resolve(),
    Path("src/claude_code/.claude/agents/madgraph-operator.md").resolve(),
]

# Transcript extraction config.
_claude_config_raw = os.environ.get("CLAUDE_CONFIG_DIR", "")
CLAUDE_CONFIG_DIR: Path | None = Path(_claude_config_raw).resolve() if _claude_config_raw else None
SESSION_ID = os.environ.get("SESSION_ID", "")

# ---------------------------------------------------------------------------
#  Vault: hide/show paths for eval isolation
# ---------------------------------------------------------------------------

_active_vault: dict | None = None  # {"token", "vault_dir", "manifest_path"}


def _vault_base_dir() -> Path:
    """Vault location on the host, outside all bind-mounted directories."""
    for prefix in ALLOWED_PREFIXES:
        if prefix in PATH_MAP:
            return Path(PATH_MAP[prefix]).parent / ".vault"
    return Path.cwd() / ".vault"


def _resolve_vault_entry(container_path: str, token: str) -> dict:
    """Build a manifest entry for one container path."""
    host_path = _to_host_path(container_path)
    rel = container_path.lstrip("/")
    vault_path = _vault_base_dir() / token / rel
    return {
        "container_path": container_path,
        "host_path": str(host_path),
        "vault_path": str(vault_path),
        "is_dir": host_path.is_dir() if host_path.exists() else False,
    }


mcp = FastMCP(name="madgraph-docs")


def _generate_diff(host_draft: Path) -> str:
    """Generate a unified diff between the real docs and a draft.

    Handles the directory structure mismatch: the draft has topic files
    under ``madgraph/`` and the overview as ``madgraph_overview.md``,
    while the real docs are at DOCS_DIR and OVERVIEW_FILE respectively.

    Returns the diff text (empty string if no changes).
    """
    docs_src = host_draft / "madgraph"
    if not docs_src.exists():
        return ""

    # Diff topic files.
    result = subprocess.run(
        ["diff", "-ruN", str(DOCS_DIR), str(docs_src)],
        capture_output=True, text=True,
    )
    diff_text = result.stdout or ""

    # Diff overview file (lives outside DOCS_DIR, renamed in draft).
    overview_src = host_draft / "madgraph_overview.md"
    if overview_src.exists() and OVERVIEW_FILE.exists():
        if overview_src.read_text() != OVERVIEW_FILE.read_text():
            overview_diff = subprocess.run(
                ["diff", "-uN", str(OVERVIEW_FILE), str(overview_src)],
                capture_output=True, text=True,
            ).stdout
            if overview_diff:
                diff_text = diff_text + "\n" + overview_diff

    return diff_text


def _validate_path(container_path: str) -> str:
    """Validate that a container path is under an allowed prefix.

    Returns an error message if invalid, empty string if OK.
    """
    for prefix in ALLOWED_PREFIXES:
        if container_path.startswith(prefix):
            return ""
    return (
        f"Error: path '{container_path}' is not allowed. "
        f"Must be under {' or '.join(ALLOWED_PREFIXES)}."
    )


def _to_host_path(container_path: str) -> Path:
    """Translate a container path to a host path."""
    for container_prefix, host_prefix in PATH_MAP.items():
        if container_path.startswith(container_prefix):
            suffix = container_path[len(container_prefix):]
            return Path(host_prefix + suffix)
    return Path(container_path)


def _rebuild_agent_card():
    """Rebuild the madgraph-operator agent card from header + overview."""
    if not AGENT_HEADER.exists() or not OVERVIEW_FILE.exists():
        return
    header = AGENT_HEADER.read_text().rstrip("\n") + "\n"
    overview = OVERVIEW_FILE.read_text()
    shifted = re.sub(r"^(#+)", r"#\1", overview, flags=re.MULTILINE)
    content = header + "\n" + shifted
    for card in AGENT_CARDS:
        if card.parent.exists():
            card.write_text(content)


@mcp.tool
def get_doc_draft(path: str) -> str:
    """Create a writable copy of the MadGraph documentation for editing.

    Copies the docs to the specified path where you can edit them
    freely. After editing, call apply_doc_changes with the same path.

    Args:
        path: Where to create the draft (must be under /workspace or /output).
              Example: /workspace/docs_draft

    Returns:
        Summary and instructions.
    """
    err = _validate_path(path)
    if err:
        return err

    host_dst = _to_host_path(path)
    if host_dst.exists():
        shutil.rmtree(host_dst)
    host_dst.mkdir(parents=True)

    # Copy docs into a madgraph/ subfolder.
    shutil.copytree(DOCS_DIR, host_dst / "madgraph")

    # Include the overview file alongside it.
    if OVERVIEW_FILE.exists():
        shutil.copy2(OVERVIEW_FILE, host_dst / "madgraph_overview.md")

    n_files = sum(1 for _ in host_dst.rglob("*.md"))
    return f"Created draft with {n_files} files at {path}."


@mcp.tool
def get_doc_diff(path: str) -> str:
    """Generate a diff between the current documentation and the edited draft.

    Compares the real docs (topic files and overview) with the draft.
    Does NOT apply any changes — use apply_doc_changes for that.

    Args:
        path: Path to the edited draft (must be under /workspace or /output).
              This should be the same path passed to get_doc_draft.

    Returns:
        Unified diff text, or a message if no changes detected.
    """
    err = _validate_path(path)
    if err:
        return err

    host_src = _to_host_path(path)
    if not (host_src / "madgraph").exists():
        return f"Error: no draft found at {path}/madgraph/. Call get_doc_draft('{path}') first."

    diff_text = _generate_diff(host_src)
    if not diff_text.strip():
        return "No changes detected in the draft."
    return diff_text


@mcp.tool
def apply_doc_changes(path: str) -> str:
    """Replace the MadGraph documentation with the edited draft.

    Reads edited files from the specified path, replaces the real
    documentation, and rebuilds the agent card.

    Args:
        path: Path to the edited draft (must be under /workspace or /output).
              This should be the same path passed to get_doc_draft.

    Returns:
        A summary of what was changed.
    """
    err = _validate_path(path)
    if err:
        return err

    host_src = _to_host_path(path)
    docs_src = host_src / "madgraph"
    if not docs_src.exists():
        return f"Error: no draft found at {path}/madgraph/. Call get_doc_draft('{path}') first."

    diff_text = _generate_diff(host_src)
    if not diff_text.strip():
        return "No changes detected in the draft."

    # Apply overview if changed.
    overview_src = host_src / "madgraph_overview.md"
    overview_changed = False
    if overview_src.exists() and OVERVIEW_FILE.exists():
        if overview_src.read_text() != OVERVIEW_FILE.read_text():
            shutil.copy2(overview_src, OVERVIEW_FILE)
            overview_changed = True

    # Replace docs directory.
    for item in DOCS_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    for item in docs_src.iterdir():
        dst = DOCS_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

    # Rebuild agent card.
    _rebuild_agent_card()

    # Clean up draft.
    shutil.rmtree(host_src, ignore_errors=True)

    n_changed = diff_text.count("\n+++ ")
    msg = f"Applied changes to {n_changed} files."
    if overview_changed:
        msg += " Updated madgraph.md overview and rebuilt agent card."

    return msg


# ---------------------------------------------------------------------------
#  Vault tools
# ---------------------------------------------------------------------------


@mcp.tool
def hide_paths(paths: list[str]) -> str:
    """Hide files/directories so they are invisible inside the container.

    Moves the host-side equivalents of the given container paths to a
    vault directory outside all bind mounts. Returns a token that must
    be passed to show_paths() to restore them.

    Args:
        paths: Container paths to hide (must be under /workspace or /output).
               Example: ["/workspace/train/q000/grade", "/workspace/train/q000/verify"]

    Returns:
        A message containing the restore token.
    """
    global _active_vault

    if _active_vault is not None:
        return (
            "Error: paths are already hidden. "
            "Call show_paths() with the previous token before hiding again."
        )

    # Validate all paths first.
    errors = []
    for p in paths:
        err = _validate_path(p)
        if err:
            errors.append(err)
    if errors:
        return "Validation errors:\n" + "\n".join(errors)

    token = str(uuid.uuid4())

    # Resolve entries, separate existing from missing.
    entries = []
    missing = []
    for p in paths:
        entry = _resolve_vault_entry(p, token)
        if Path(entry["host_path"]).exists():
            entries.append(entry)
        else:
            missing.append(p)

    if not entries:
        # Nothing to hide, but still return a valid token.
        _active_vault = {"token": token, "vault_dir": None, "manifest_path": None}
        msg = f"No existing paths to hide (token: {token})."
        if missing:
            msg += f" Skipped {len(missing)} non-existent paths."
        return msg

    # Create vault directory.
    vault_dir = _vault_base_dir() / token
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Move files with rollback on failure.
    moved: list[tuple[Path, Path]] = []  # (host_path, vault_path)
    try:
        for entry in entries:
            host_path = Path(entry["host_path"])
            vault_path = Path(entry["vault_path"])
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(host_path), str(vault_path))
            moved.append((host_path, vault_path))
    except Exception as exc:
        # Roll back successful moves.
        for host_path, vault_path in reversed(moved):
            try:
                host_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(vault_path), str(host_path))
            except Exception:
                pass
        shutil.rmtree(vault_dir, ignore_errors=True)
        return f"Error: failed to hide paths (rolled back). {exc}"

    # Write manifest.
    manifest = {
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    manifest_path = vault_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    _active_vault = {
        "token": token,
        "vault_dir": vault_dir,
        "manifest_path": manifest_path,
    }

    msg = f"Hidden {len(entries)} paths (token: {token})."
    if missing:
        msg += f" Skipped {len(missing)} non-existent paths."
    return msg


@mcp.tool
def show_paths(token: str) -> str:
    """Restore previously hidden files/directories.

    Validates the token and moves all hidden paths back to their
    original host locations.

    Args:
        token: The restore token returned by hide_paths().

    Returns:
        A summary of restored paths.
    """
    global _active_vault

    # Try in-memory state first.
    if _active_vault is not None:
        if _active_vault["token"] != token:
            return "Error: invalid token."
        vault_dir = _active_vault["vault_dir"]
        manifest_path = _active_vault["manifest_path"]
    else:
        # Try loading from disk (crash recovery after recover_vault).
        vault_dir = _vault_base_dir() / token
        manifest_path = vault_dir / "manifest.json" if vault_dir else None
        if manifest_path is None or not manifest_path.exists():
            return "Error: no active vault or invalid token."

    # No-op vault (nothing was actually hidden).
    if vault_dir is None:
        _active_vault = None
        return "Nothing to restore (no paths were hidden)."

    if not manifest_path.exists():
        _active_vault = None
        return "Error: manifest not found. Vault may have been cleaned up."

    manifest = json.loads(manifest_path.read_text())
    if manifest["token"] != token:
        return "Error: token mismatch with manifest."

    # Restore files.
    restored = 0
    errors = []
    for entry in manifest["entries"]:
        vault_path = Path(entry["vault_path"])
        host_path = Path(entry["host_path"])
        if not vault_path.exists():
            errors.append(f"  Missing from vault: {entry['container_path']}")
            continue
        try:
            host_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(vault_path), str(host_path))
            restored += 1
        except Exception as exc:
            errors.append(f"  Failed to restore {entry['container_path']}: {exc}")

    # Clean up vault directory.
    shutil.rmtree(vault_dir, ignore_errors=True)
    _active_vault = None

    msg = f"Restored {restored} paths."
    if errors:
        msg += "\nWarnings:\n" + "\n".join(errors)
    return msg


@mcp.tool
def recover_vault() -> str:
    """List vaults from previous hide_paths() calls (for crash recovery).

    Scans for existing vault directories and loads them so show_paths()
    can be called. Does NOT auto-restore — call show_paths(token) after.

    Returns:
        Summary of found vaults with their tokens.
    """
    global _active_vault

    base = _vault_base_dir()
    if not base.exists():
        return "No vault directory found."

    found = []
    for child in sorted(base.iterdir()):
        manifest_path = child / "manifest.json"
        if child.is_dir() and manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                found.append({
                    "token": manifest["token"],
                    "created_at": manifest.get("created_at", "unknown"),
                    "entries": len(manifest.get("entries", [])),
                    "vault_dir": str(child),
                })
            except Exception:
                found.append({
                    "token": child.name,
                    "created_at": "unknown",
                    "entries": "?",
                    "vault_dir": str(child),
                    "error": "Failed to read manifest",
                })

    if not found:
        return "No vaults found."

    # Load the most recent vault into _active_vault.
    latest = found[-1]
    if "error" not in latest:
        _active_vault = {
            "token": latest["token"],
            "vault_dir": Path(latest["vault_dir"]),
            "manifest_path": Path(latest["vault_dir"]) / "manifest.json",
        }

    lines = [f"Found {len(found)} vault(s):"]
    for v in found:
        lines.append(
            f"  token: {v['token']}  created: {v['created_at']}  "
            f"entries: {v['entries']}"
        )
    if _active_vault:
        lines.append(f"\nLoaded latest vault. Call show_paths(\"{_active_vault['token']}\") to restore.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  Transcript extraction
# ---------------------------------------------------------------------------


def _clean_message(entry: dict) -> dict | None:
    """Strip metadata from a transcript entry, keeping only workflow content.

    Returns None for events that should be dropped entirely.
    Ported from src/eval/transcript.py.
    """
    if not isinstance(entry, dict):
        return None

    t = entry.get("type", "")

    # Drop entirely.
    if t == "rate_limit_event":
        return None
    if t == "system" and entry.get("subtype") == "init":
        return None

    # Our recorded user prompt — keep as-is.
    if t == "user" and "prompt" in entry:
        return {"type": "user", "prompt": entry["prompt"]}

    # User messages (tool results) — keep tool_use_id, type, content.
    if t == "user" and "message" in entry:
        msg = entry["message"]
        content = msg.get("content", [])
        if isinstance(content, str):
            return {"type": "user", "message": {"role": "user", "content": content}}
        cleaned_content = []
        for block in content:
            if block.get("type") == "tool_result":
                cleaned = {
                    "type": "tool_result",
                    "tool_use_id": block.get("tool_use_id"),
                }
                if "content" in block:
                    cleaned["content"] = block["content"]
                cleaned_content.append(cleaned)
            else:
                cleaned_content.append(block)
        return {"type": "user", "message": {"role": "user", "content": cleaned_content}}

    # Assistant messages — keep text, tool_use, thinking text; strip metadata.
    if t == "assistant":
        msg = entry.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, str):
            return {"type": "assistant", "content": [{"type": "text", "text": content}]} if content.strip() else None
        cleaned_content = []
        for block in content:
            bt = block.get("type", "")
            if bt == "text":
                text = block.get("text", "").strip()
                if text:
                    cleaned_content.append({"type": "text", "text": text})
            elif bt == "tool_use":
                cleaned = {
                    "type": "tool_use",
                    "id": block.get("id"),
                    "name": block.get("name"),
                }
                if "input" in block:
                    cleaned["input"] = block["input"]
                cleaned_content.append(cleaned)
            elif bt == "thinking":
                thinking = block.get("thinking", "").strip()
                if thinking:
                    cleaned_content.append({"type": "thinking", "thinking": thinking})
        if not cleaned_content:
            return None
        result: dict = {"type": "assistant", "content": cleaned_content}
        pid = entry.get("parent_tool_use_id")
        if pid:
            result["parent_tool_use_id"] = pid
        return result

    # System task events (subagent lifecycle) — keep.
    if t == "system" and entry.get("subtype") in ("task_started", "task_completed"):
        cleaned: dict = {"type": "system", "subtype": entry["subtype"]}
        for key in ("task_id", "tool_use_id", "description", "task_type", "prompt", "result"):
            if key in entry:
                cleaned[key] = entry[key]
        return cleaned

    # Result event — keep summary, drop usage details.
    if t == "result":
        cleaned = {"type": "result"}
        for key in ("result", "is_error", "session_id", "num_turns", "duration_ms", "cost_usd"):
            if key in entry:
                cleaned[key] = entry[key]
        return cleaned

    # Unknown event types — drop.
    return None


def _find_subagent_transcript(description: str) -> Path | None:
    """Find the JSONL transcript for a subagent matching *description*.

    Searches subagent meta.json files under all project sessions.
    """
    if CLAUDE_CONFIG_DIR is None:
        return None

    projects_dir = CLAUDE_CONFIG_DIR / "projects"
    if not projects_dir.exists():
        return None

    # Search all sessions (SESSION_ID from --session-id may not match
    # the internal file naming).
    pattern = "*/*/subagents/agent-*.meta.json"

    best: Path | None = None
    best_mtime = 0.0

    for meta_path in sorted(projects_dir.glob(pattern)):
        try:
            meta = json.loads(meta_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if meta.get("description") == description:
            jsonl_path = meta_path.with_suffix(".jsonl")
            if jsonl_path.exists():
                mtime = jsonl_path.stat().st_mtime
                if mtime > best_mtime:
                    best = jsonl_path
                    best_mtime = mtime

    return best


def _find_teammate_transcript(team_name: str, agent_name: str) -> Path | None:
    """Find the JSONL transcript for a teammate session.

    Teammates are stored as separate top-level sessions (not under
    subagents/). Each message carries ``teamName`` and ``agentName``.
    We read only the first few lines of each candidate to check.
    """
    if CLAUDE_CONFIG_DIR is None:
        return None

    projects_dir = CLAUDE_CONFIG_DIR / "projects"
    if not projects_dir.exists():
        return None

    best: Path | None = None
    best_mtime = 0.0

    for jsonl_path in projects_dir.glob("*/*.jsonl"):
        # Skip subagent transcripts.
        if "subagents" in str(jsonl_path):
            continue
        try:
            with open(jsonl_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(entry, dict):
                        continue
                    # Check the first entry that carries team info.
                    if "teamName" in entry:
                        if (entry.get("teamName") == team_name
                                and entry.get("agentName") == agent_name):
                            mtime = jsonl_path.stat().st_mtime
                            if mtime > best_mtime:
                                best = jsonl_path
                                best_mtime = mtime
                        break  # Only need to check the first team entry.
                    # Non-team entry (e.g. permission-mode) — skip to next.
                    if entry.get("type") not in ("permission-mode",):
                        break  # Not a teammate session.
        except OSError:
            continue

    return best


def _extract_answer(jsonl_path: Path) -> str:
    """Extract the answer from a transcript by collecting assistant text blocks.

    Mirrors the eval pipeline approach: all user-facing assistant text
    blocks are collected and joined with double newlines.
    """
    texts: list[str] = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, str):
                    if content.strip():
                        texts.append(content.strip())
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            texts.append(text)
    except OSError:
        pass
    return "\n\n".join(texts)


@mcp.tool
def get_transcript(
    output_path: str,
    description: str = "",
    team_name: str = "",
    agent_name: str = "",
    answer_path: str = "",
) -> str:
    """Extract and clean a subagent or teammate conversation transcript.

    Two lookup modes:
    - **Subagent**: pass ``description`` — matches the Agent tool description
      in ``.meta.json`` files under the session's ``subagents/`` directory.
    - **Teammate**: pass ``team_name`` and ``agent_name`` — finds the
      teammate's own session by matching ``teamName`` and ``agentName``
      fields in the transcript JSONL.

    If ``answer_path`` is provided, also extracts the answer (all
    assistant text blocks joined) and writes it as a markdown file.

    Args:
        output_path: Where to write the cleaned transcript JSON
                     (must be under /workspace or /output).
        description: The Agent tool description used when spawning
                     the subagent (for subagent lookup).
        team_name: Team name (for teammate lookup).
        agent_name: Teammate name within the team (for teammate lookup).
        answer_path: Where to write the extracted answer as markdown
                     (must be under /workspace or /output). Optional.

    Returns:
        Summary message or error.
    """
    err = _validate_path(output_path)
    if err:
        return err
    if answer_path:
        err = _validate_path(answer_path)
        if err:
            return err

    if CLAUDE_CONFIG_DIR is None:
        return "Error: CLAUDE_CONFIG_DIR not configured. Cannot find transcripts."

    # Determine lookup mode.
    if team_name and agent_name:
        jsonl_path = _find_teammate_transcript(team_name, agent_name)
        lookup_desc = f"teammate {agent_name} in team {team_name}"
    elif description:
        jsonl_path = _find_subagent_transcript(description)
        lookup_desc = f"subagent with description: {description!r}"
    else:
        return "Error: provide either (team_name + agent_name) or description."

    if jsonl_path is None:
        return f"Error: no transcript found for {lookup_desc}"

    # Read and clean events.
    events = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cleaned = _clean_message(event)
                if cleaned is not None:
                    events.append(cleaned)
    except OSError as exc:
        return f"Error reading transcript: {exc}"

    # Write cleaned transcript.
    host_dst = _to_host_path(output_path)
    host_dst.parent.mkdir(parents=True, exist_ok=True)
    host_dst.write_text(json.dumps(events, indent=2))

    msg = f"Wrote {len(events)} cleaned events to {output_path}."

    # Extract and write answer if requested.
    if answer_path:
        answer = _extract_answer(jsonl_path)
        host_answer = _to_host_path(answer_path)
        host_answer.parent.mkdir(parents=True, exist_ok=True)
        host_answer.write_text(answer)
        msg += f" Wrote answer ({len(answer)} chars) to {answer_path}."

    return msg


if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", "8089"))
    mcp.run(transport="streamable-http", host="127.0.0.1", port=port)
