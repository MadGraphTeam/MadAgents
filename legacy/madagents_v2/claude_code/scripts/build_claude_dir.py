#!/usr/bin/env python3
"""Build a .claude/ directory for a session.

Centralizes .claude/ construction for all consumers:
- madrun_code.sh (interactive MadAgents)
- eval pipeline (session.py)
- eval examples (container.sh)

Usage as script:
    python3 build_claude_dir.py <dst> [--type bare|madagents] [--doc-editing]

Usage as library:
    from scripts.build_claude_dir import build_claude_dir
    build_claude_dir(dst, session_type="madagents", doc_editing=True)
"""

import argparse
import shutil
from pathlib import Path

CLAUDE_CODE_DIR = Path(__file__).resolve().parent.parent
SOURCE = CLAUDE_CODE_DIR / ".claude"

# Loaded when --verify is enabled (verification via verifier agent).
VERIFY_AGENTS = {"claim-extractor.md", "verifier.md"}

# Skills kept in source but never deployed (verification is handled by
# the verifier agent, not a skill).
EXCLUDED_SKILLS = {"verify-claims"}

# Loaded when doc editing is enabled (implies --verify).
DOC_EDITING_SKILLS = {
    "edit-docs", "get-docs", "train-docs", "diagnose-docs", "generate-questions",
}
DOC_EDITING_RULES = {"docs-editing.md"}
DOC_EDITING_AGENTS = {
    "doc-editor.md", "doc-style-reviewer.md", "doc-quality-reviewer.md",
    "grader.md", "claim-triage.md", "claim-remember.md",
    "orchestrator.md",
}


def _place(src: Path, dst: Path, symlink: bool) -> None:
    """Copy or symlink a file."""
    if symlink:
        dst.symlink_to(src.resolve())
    else:
        shutil.copy2(src, dst)


def _place_tree(src: Path, dst: Path, symlink: bool) -> None:
    """Copy or symlink a directory tree.

    With symlink=True, creates real directories but symlinks leaf files.
    This lets the container traverse the directory structure while edits
    to individual files persist to the source.
    """
    if symlink:
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            rel = item.relative_to(src)
            target = dst / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.symlink_to(item.resolve())
    else:
        shutil.copytree(src, dst)


def build_claude_dir(
    dst: str | Path,
    *,
    session_type: str = "madagents",
    verify: bool = False,
    doc_editing: bool = False,
    no_skills: bool = False,
    symlink: bool = False,
    append_system_prompt: str | Path | None = None,
) -> Path:
    """Build a .claude/ directory at *dst*.

    Parameters
    ----------
    dst : path
        Target directory. Created if it doesn't exist; existing contents
        are overwritten.
    session_type : "bare" or "madagents"
        - bare: settings.local.json only (for graders, verifiers, etc.)
        - madagents: full setup (settings, CLAUDE.md, agents, skills, rules)
    verify : bool
        If True, include the verifier and claim-extractor agents.
        Implied by doc_editing.
    doc_editing : bool
        If True, include doc-editing skills, rules, and eval subagents.
        Also enables agent teams env and MCP permissions.
        Implies verify=True. Only relevant for session_type="madagents".
    no_skills : bool
        If True, skip all skills.
    symlink : bool
        If True, symlink files instead of copying. Edits in the session
        persist to the source. Use for interactive sessions (madrun_code.sh).
    append_system_prompt : path, optional
        Path to a file whose contents are appended to CLAUDE.md.
        Useful for baking orchestrator instructions so that teammates
        (which share the lead's CWD and .claude/) also see them.

    Returns
    -------
    Path to the created .claude/ directory.
    """
    if doc_editing:
        verify = True

    dst = Path(dst)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    # ── Always: settings ─────────────────────────────────────────────
    import json

    settings = SOURCE / "settings.local.json"
    if doc_editing:
        settings_data = json.loads(settings.read_text()) if settings.exists() else {}
    elif settings.exists():
        _place(settings, dst / "settings.local.json", symlink)
        settings_data = None
    else:
        settings_data = None

    # When doc_editing is on, add MCP permissions and agent teams env.
    if doc_editing and settings_data is not None:
        # Allow MCP tools (except apply_doc_changes, which needs user confirmation).
        perms = settings_data.setdefault("permissions", {})
        allow = perms.setdefault("allow", [])
        for rule in [
            "mcp__madgraph-docs__get_doc_draft",
            "mcp__madgraph-docs__get_doc_diff",
            "mcp__madgraph-docs__hide_paths",
            "mcp__madgraph-docs__show_paths",
            "mcp__madgraph-docs__recover_vault",
            "mcp__madgraph-docs__get_transcript",
        ]:
            if rule not in allow:
                allow.append(rule)
        # Enable agent teams so teammates can be spawned.
        env = settings_data.setdefault("env", {})
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        # Disable auto-memory to prevent training contamination.
        settings_data["autoMemoryEnabled"] = False

    if settings_data is not None:
        (dst / "settings.local.json").write_text(
            json.dumps(settings_data, indent=2) + "\n"
        )

    if session_type == "bare":
        return dst

    # ── MadAgents: CLAUDE.md ─────────────────────────────────────────
    claude_md = SOURCE / "CLAUDE.md"
    if claude_md.exists():
        if append_system_prompt:
            # Copy + append: can't use symlink since we're modifying content.
            dst_claude_md = dst / "CLAUDE.md"
            dst_claude_md.write_text(
                claude_md.read_text()
                + "\n"
                + Path(append_system_prompt).read_text()
            )
        else:
            _place(claude_md, dst / "CLAUDE.md", symlink)

    # ── MadAgents: agents ────────────────────────────────────────────
    agents_src = SOURCE / "agents"
    if agents_src.is_dir():
        agents_dst = dst / "agents"
        agents_dst.mkdir()
        for f in agents_src.iterdir():
            if not verify and f.name in VERIFY_AGENTS:
                continue
            if not doc_editing and f.name in DOC_EDITING_AGENTS:
                continue
            if f.is_dir():
                _place_tree(f, agents_dst / f.name, symlink)
            elif f.is_file():
                _place(f, agents_dst / f.name, symlink)

    # ── MadAgents: rules ─────────────────────────────────────────────
    rules_src = SOURCE / "rules"
    if rules_src.is_dir():
        rules_dst = dst / "rules"
        rules_dst.mkdir()
        for f in rules_src.iterdir():
            if not doc_editing and f.name in DOC_EDITING_RULES:
                continue
            if f.is_file():
                _place(f, rules_dst / f.name, symlink)

    # ── MadAgents: skills ────────────────────────────────────────────
    skills_src = SOURCE / "skills"
    if no_skills:
        pass
    elif skills_src.is_dir():
        skills_dst = dst / "skills"
        skills_dst.mkdir()
        for skill_dir in skills_src.iterdir():
            if not skill_dir.is_dir():
                continue
            if skill_dir.name in EXCLUDED_SKILLS:
                continue
            if not doc_editing and skill_dir.name in DOC_EDITING_SKILLS:
                continue
            _place_tree(skill_dir, skills_dst / skill_dir.name, symlink)

    return dst


def main():
    parser = argparse.ArgumentParser(description="Build a .claude/ directory.")
    parser.add_argument("dst", help="Target directory path")
    parser.add_argument(
        "--type", dest="session_type", default="madagents",
        choices=["bare", "madagents"],
        help="Session type (default: madagents)",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Include madagents-verifier and claim-extractor agents",
    )
    parser.add_argument(
        "--doc-editing", action="store_true",
        help="Include doc-editing skills, rules, eval subagents, and agent teams (implies --verify)",
    )
    parser.add_argument(
        "--no-skills", action="store_true",
        help="Skip all skills",
    )
    parser.add_argument(
        "--symlink", action="store_true",
        help="Symlink files instead of copying (edits persist to source)",
    )
    parser.add_argument(
        "--append-system-prompt", dest="append_system_prompt", default=None,
        help="Path to file whose contents are appended to CLAUDE.md",
    )
    args = parser.parse_args()

    result = build_claude_dir(
        args.dst,
        session_type=args.session_type,
        verify=args.verify,
        doc_editing=args.doc_editing,
        no_skills=args.no_skills,
        symlink=args.symlink,
        append_system_prompt=args.append_system_prompt,
    )
    print(f"Built {result}")


if __name__ == "__main__":
    main()
