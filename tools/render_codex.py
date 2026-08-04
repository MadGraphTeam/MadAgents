#!/usr/bin/env python3
"""Render the Claude Code agent system into its Codex form.

    python3 tools/render_codex.py            # regenerate madagents_codex/
    python3 tools/render_codex.py --check    # fail if the tracked tree is stale

``madagents/`` is the canonical system: hand-edited, and edited by the agents
themselves through ``/ma-doctor``. ``madagents_codex/`` is **generated from
it** and tracked so a reviewer can diff what actually ships to Codex. Never
hand-edit the output; change the canonical tree (or an override) and re-render.

Three kinds of transformation, in increasing order of how much they know:

1. **Mechanical** — cards become ``.codex/agents/<name>.toml``, skills move to
   ``.agents/skills/`` (Codex's repo-scoped skill root; the ``SKILL.md`` format
   is identical, so they copy verbatim).

2. **Substitution** — the path strings whose *referent* moves but whose
   sentence still reads correctly. The lead's slate is the clean case: a
   markdown file either way, just at a different path.

3. **Overrides** — files whose *mechanism* differs, where rewriting a path
   would leave a sentence that is well-formed and wrong. A consultant's slate
   is not at a path on Codex; it is a marked region of the role file, written
   through a script. No substitution expresses that, so those files are
   hand-written under ``tools/codex_overrides/`` and pinned to the SHA-256 of
   the source they were written against. Edit the canonical file and the
   render **fails** until someone revisits the override — which is the whole
   point: an override is a fork, and a silently stale fork is how the two
   providers drift apart.
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import re
import shutil
import sys
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher.codex_memory import (  # noqa: E402
    COLD_SLATE,
    SLATE_BEGIN,
    SLATE_END,
    SLATE_PREAMBLE,
)

SRC = REPO_ROOT / "madagents"
OUT = REPO_ROOT / "madagents_codex"
OVERRIDES = REPO_ROOT / "tools" / "codex_overrides"
ASSETS = REPO_ROOT / "tools" / "codex_assets"
OVERRIDE_MANIFEST = OVERRIDES / "OVERRIDES.toml"

#: TOML multi-line literal strings take no escapes — which is exactly why the
#: cards' LaTeX (``\alpha``, ``\sqrt{s}``) survives — but they cannot contain
#: the delimiter, and cannot end with a quote.
LITERAL = "'''"


class RenderError(RuntimeError):
    pass


def assert_safe_output(out: Path, marker: str) -> None:
    """Refuse to wipe an output directory that is not a previous render.

    ``render_tree`` removes ``out`` wholesale before writing, which is right for
    the tracked tree and catastrophic anywhere else: ``--out ~/notes`` would
    take that directory with it, silently and without a prompt. Accept the path
    only when there is nothing to lose — it does not exist, or it is empty — or
    when it carries ``marker``, the subdirectory only a render of this tree
    creates.

    Provider-neutral, so the caller supplies the marker: ``.codex/agents`` for
    the Codex tree, ``.opencode/cards`` for the opencode one.
    """
    if not out.exists():
        return
    if not out.is_dir():
        raise RenderError(f"--out {out} exists and is not a directory")
    if not any(out.iterdir()):
        return
    if not (out / marker).is_dir():
        raise RenderError(
            f"--out {out} is not empty and has no {marker}/ inside it, so it is not "
            f"a previous render of this tree. Rendering starts by deleting the "
            f"output directory, so this would destroy it. Point --out at an empty "
            f"directory, or remove that one yourself first."
        )


# ---------------------------------------------------------------- substitution

#: The slate sentence, carried identically by 41 of the 46 cards. On Codex the
#: slate is not at a path, so the *path token* is what gets replaced; the rest
#: of the sentence (budget, section list, "match the index") is true either way.
_SLATE_PATH = re.compile(r"`\.claude/agent-memory/[a-z0-9-]+/MEMORY\.md`")
_SLATE_REPLACEMENT = "the marked slate region at the end of this file"

#: The lead's slate stays an ordinary markdown file — the launcher concatenates
#: it onto the lead's developer instructions at start-up — so this one really
#: is just a path move.
_LEAD_SLATE = ".claude/lead-memory/MEMORY.md"
_LEAD_SLATE_CODEX = ".madagents/memory/lead/MEMORY.md"


def substitute(text: str) -> str:
    """Apply the path rewrites that leave a sentence true as well as well-formed."""
    text = text.replace(_LEAD_SLATE, _LEAD_SLATE_CODEX)
    return _SLATE_PATH.sub(_SLATE_REPLACEMENT, text)


#: ``ma-doctor/lessons/`` is a **citation corpus** — agent-design principles
#: distilled from named books, each carrying a bibliographic reference. Some
#: cite Claude Code by name because that is what the cited author actually did
#: ("the author added a rule to CLAUDE.md after each mistake"). Rewriting those
#: would not port a path, it would falsify a citation. So the corpus is exempt
#: from the check, and the one lesson whose *own* prose is harness-specific is
#: handled the honest way — as an override.
_CITATION_CORPUS = ".claude/skills/ma-doctor/lessons/"


def assert_no_stale_paths(rel: str, text: str) -> None:
    """Catch a `.claude/` reference no rule and no override accounted for.

    A missed one is silent at render time and wrong at run time — it sends an
    agent to a path that does not exist in a Codex install.
    """
    if rel.startswith(_CITATION_CORPUS):
        return
    if ".claude/" in text or "CLAUDE.md" in text:
        stale = sorted({m for m in re.findall(r"[`\s(]([^`\s()]*(?:\.claude/|CLAUDE\.md)[^`\s()]*)", text)})
        raise RenderError(
            f"{rel}: Claude Code path(s) survived rendering: {stale}. "
            f"Add a substitution rule, or an override in tools/codex_overrides/."
        )


# ------------------------------------------------------------------- overrides


def load_overrides() -> dict[str, dict]:
    """Read the override manifest: source path -> {sha256, renames_to?}."""
    if not OVERRIDE_MANIFEST.is_file():
        return {}
    data = tomllib.loads(OVERRIDE_MANIFEST.read_text(encoding="utf-8"))
    return data.get("override", {})


def override_for(rel: str, overrides: dict[str, dict]) -> tuple[Path, str] | None:
    """Return (override file, output relative path) for *rel*, or None.

    Verifies the pin first. The pin is the mechanism that keeps an override
    honest: it records the canonical file the override was written against, so
    editing the canonical file surfaces every fork that now needs revisiting
    instead of letting them rot.
    """
    entry = overrides.get(rel)
    if entry is None:
        return None
    src = SRC / rel
    actual = hashlib.sha256(src.read_bytes()).hexdigest()
    if actual != entry["sha256"]:
        raise RenderError(
            f"{rel} changed since its Codex override was written.\n"
            f"  expected sha256 {entry['sha256']}\n"
            f"  actual   sha256 {actual}\n"
            f"Re-read tools/codex_overrides/{entry.get('renames_to', rel)}, fold in the change, "
            f"then update the sha256 in tools/codex_overrides/OVERRIDES.toml."
        )
    override_path = OVERRIDES / entry.get("renames_to", rel)
    if not override_path.is_file():
        raise RenderError(f"{rel}: manifest names an override that does not exist: {override_path}")
    return override_path, entry.get("renames_to", rel)


# ----------------------------------------------------------------------- cards


def normalize_skill(text: str, rel: str) -> str:
    """Re-emit a SKILL.md's frontmatter as valid YAML.

    Claude Code's frontmatter reader is lenient; Codex's is a real YAML parser,
    and it does not merely complain — it **drops the skill from the list with no
    error**, so the workflow silently stops being discoverable. Two of the eight
    shipped skills hit this today, ``mg-setup`` and ``ma-wiki-write``, both for
    the same reason: an unquoted scalar containing ``": "`` (*"the deliverable
    is an MG5 setup: the process line…"*), which YAML reads as a nested mapping.

    Rather than depend on nobody ever writing a colon again — these
    descriptions are edited by hand and by ``/ma-doctor`` — the renderer emits
    the frontmatter through a YAML dumper, which quotes whatever needs quoting,
    and then parses the result back to prove it.
    """
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise RenderError(f"{rel}: no YAML frontmatter")
    fields = read_frontmatter(m.group(1), rel)
    for required in ("name", "description"):
        if not fields.get(required):
            raise RenderError(f"{rel}: frontmatter missing {required!r}")
    front = yaml.safe_dump(
        fields, sort_keys=False, allow_unicode=True, width=10**9, default_flow_style=False,
    ).strip()
    out = f"---\n{front}\n---\n{m.group(2)}"

    check = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", out, re.S).group(1))
    if not isinstance(check, dict) or not isinstance(check.get("description"), str):
        raise RenderError(f"{rel}: frontmatter still does not parse as YAML after normalising")
    if check["description"] != fields["description"]:
        raise RenderError(f"{rel}: description did not survive the YAML round-trip")
    return out


def read_frontmatter(front: str, what: str) -> dict[str, str]:
    """Read ``key: value`` frontmatter, block scalars included, verbatim.

    Deliberately not a YAML parse: the point is to read the description
    *exactly as written* — including the forms YAML rejects — so the renderer
    can re-emit it correctly. A YAML round-trip here would either fail on the
    malformed ones or reflow the block scalars the 46 cards use.
    """
    fields: dict[str, str] = {}
    key = None
    block: list[str] = []
    for line in front.split("\n"):
        m_key = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m_key and not line.startswith((" ", "\t")):
            if key is not None:
                fields[key] = "\n".join(block).strip()
            key, rest = m_key.group(1), m_key.group(2).strip()
            block = [] if rest in ("|", ">", "") else [rest]
        else:
            block.append(line.strip())
    if key is not None:
        fields[key] = "\n".join(block).strip()
    if not fields:
        raise RenderError(f"{what}: empty frontmatter")
    return fields


def parse_card(path: Path) -> tuple[dict[str, str], str]:
    """Split a card into (frontmatter fields, body).

    All 46 descriptions are YAML block scalars (``description: |``), so this
    reads the frontmatter directly rather than through a YAML parser: the aim
    is to preserve the description *verbatim*, and a YAML round-trip reflows
    it. Only three keys matter (``name``, ``description``, ``memory``) and the
    shape is uniform, so a small reader beats a dependency here.
    """
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise RenderError(f"{path}: no YAML frontmatter")
    body = m.group(2)
    fields = read_frontmatter(m.group(1), str(path))

    for required in ("name", "description"):
        if not fields.get(required):
            raise RenderError(f"{path}: frontmatter missing {required!r}")
    if fields["name"] != path.stem:
        raise RenderError(f"{path}: name {fields['name']!r} does not match filename")
    return fields, body.strip("\n")


def toml_literal(value: str, what: str) -> str:
    """Wrap *value* in a TOML multi-line literal string."""
    if LITERAL in value:
        raise RenderError(f"{what}: contains {LITERAL!r}, which cannot appear in a TOML literal string")
    if value.endswith("'"):
        value += "\n"
    return f"{LITERAL}\n{value}\n{LITERAL}"


def toml_basic(value: str) -> str:
    """A single-line TOML basic string, escaped."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")
    return f'"{escaped}"'


def render_card(path: Path, overrides: dict[str, dict]) -> tuple[str, str]:
    """Render one card to (output filename, TOML text)."""
    rel = f".claude/agents/{path.name}"
    over = override_for(rel, overrides)
    if over is not None:
        return f"{path.stem}.toml", over[0].read_text(encoding="utf-8")

    fields, body = parse_card(path)
    name = fields["name"]
    body = substitute(body)
    description = " ".join(substitute(fields["description"]).split())
    assert_no_stale_paths(rel, body + description)

    # The five reviewer/auditor cards carry no `memory:` — they are dispatched
    # fresh every time and hold no learned tier, so they get no slate region.
    instructions = body
    if fields.get("memory"):
        instructions = f"{body}\n\n{SLATE_PREAMBLE}\n\n{SLATE_BEGIN}\n{COLD_SLATE}{SLATE_END}"

    text = (
        f"# Generated by tools/render_codex.py from madagents/{rel} — do not hand-edit.\n"
        f"# The slate region below is the exception: it is the agent's own, written\n"
        f"# at runtime through .agents/skills/ma-wiki-write/scripts/write_slate.py.\n"
        f"name = {toml_basic(name)}\n"
        f"description = {toml_basic(description)}\n"
        f"developer_instructions = {toml_literal(instructions, str(path))}\n"
    )
    return f"{name}.toml", text


# ---------------------------------------------------------------------- render


#: Scalar settings Codex recognises under ``[agents]``. Anything else there is
#: read as a **custom agent role**, so a stray top-level key that drifted below
#: the ``[agents]`` header makes Codex reject the whole config with
#: "invalid type: … expected struct AgentRoleToml" — and the key it was meant to
#: set silently does nothing. This has happened once; hence the assertion.
_AGENTS_SCALARS = {
    "enabled", "max_concurrent_threads_per_session", "max_threads",
    "default_subagent_model", "default_subagent_reasoning_effort", "interrupt_message",
}


def check_codex_config(path: Path) -> None:
    """Assert the shipped project config says what it looks like it says."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise RenderError(f"{path}: not valid TOML ({exc})") from exc

    stray = [k for k, v in data.get("agents", {}).items()
             if k not in _AGENTS_SCALARS and not isinstance(v, dict)]
    if stray:
        raise RenderError(
            f"{path}: {stray} sit under [agents] but are not agent settings — Codex will "
            f"read them as custom agent roles and refuse the file. In TOML every key after "
            f"a [table] header belongs to that table: move top-level keys above [agents]."
        )
    # The shipped system pre-approves nothing, on either provider. A permission
    # profile or a sandbox mode here would make Codex the one place in the repo
    # that grants something up front, silently and for every install.
    granted = [k for k in ("default_permissions", "permissions", "sandbox_mode",
                           "sandbox_workspace_write", "approval_policy") if k in data]
    if granted:
        raise RenderError(
            f"{path}: {granted} pre-approve tool use. The Claude Code side ships no "
            f"permissions block and no launcher flags; Codex must match. Users opt out "
            f"of prompting per run with --dangerously-bypass-approvals-and-sandbox."
        )


def render_tree(out: Path) -> None:
    # Preconditions FIRST — before the rmtree below.
    assert_safe_output(out, ".codex/agents")
    overrides = load_overrides()
    used: set[str] = set()

    if out.exists():
        shutil.rmtree(out)
    (out / ".codex" / "agents").mkdir(parents=True)
    (out / ".agents" / "skills").mkdir(parents=True)
    (out / "prompts").mkdir()

    # --- cards
    cards = sorted((SRC / ".claude" / "agents").glob("*.md"))
    if not cards:
        raise RenderError(f"no cards found in {SRC / '.claude' / 'agents'}")
    for card in cards:
        rel = f".claude/agents/{card.name}"
        if rel in overrides:
            used.add(rel)
        filename, text = render_card(card, overrides)
        (out / ".codex" / "agents" / filename).write_text(text, encoding="utf-8")

    # --- skills
    skills_src = SRC / ".claude" / "skills"
    for src_file in sorted(skills_src.rglob("*")):
        if src_file.is_dir():
            continue
        rel = f".claude/skills/{src_file.relative_to(skills_src)}"
        over = override_for(rel, overrides)
        if over is not None:
            used.add(rel)
            override_path, renamed = over
            dest = out / ".agents" / "skills" / Path(renamed).relative_to(".claude/skills")
            dest.parent.mkdir(parents=True, exist_ok=True)
            text = override_path.read_text(encoding="utf-8")
            # Overrides go through the same YAML normalisation: a hand-written
            # description is exactly as able to contain an unquoted colon.
            if dest.name == "SKILL.md":
                text = normalize_skill(text, f"override:{renamed}")
            dest.write_text(text, encoding="utf-8")
            continue
        dest = out / ".agents" / "skills" / src_file.relative_to(skills_src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src_file.suffix == ".md":
            text = substitute(src_file.read_text(encoding="utf-8"))
            assert_no_stale_paths(rel, text)
            if src_file.name == "SKILL.md":
                text = normalize_skill(text, rel)
            dest.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src_file, dest)

    # --- lead prompt (substituted: the lead's slate is a real file either way)
    lead_src = SRC / "prompts" / "lead-discipline.md"
    lead_text = substitute(lead_src.read_text(encoding="utf-8"))
    assert_no_stale_paths("prompts/lead-discipline.md", lead_text)
    (out / "prompts" / "lead-discipline.md").write_text(lead_text, encoding="utf-8")

    # --- static assets
    for asset, dest_rel in (
        ("config.toml", ".codex/config.toml"),
        ("AGENTS.md.seed", "AGENTS.md.seed"),
        ("config.yaml", "config.yaml"),
    ):
        dest = out / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((ASSETS / asset).read_text(encoding="utf-8"), encoding="utf-8")
    check_codex_config(out / ".codex" / "config.toml")

    # --- the runtime slate writer, bundled with the skill that calls it
    scripts = out / ".agents" / "skills" / "ma-wiki-write" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / "write_slate.py", scripts / "write_slate.py")
    (scripts / "write_slate.py").chmod(0o755)
    shutil.copy2(REPO_ROOT / "src" / "launcher" / "codex_memory.py", scripts / "codex_memory.py")

    unused = sorted(set(overrides) - used)
    if unused:
        raise RenderError(
            f"override manifest names files that were never rendered: {unused}. "
            f"Remove the entry, or fix the path."
        )


def dirs_differ(a: Path, b: Path) -> list[str]:
    """Relative paths that differ between two trees."""
    diffs: list[str] = []
    a_files = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    b_files = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    diffs += [f"only in tracked: {p}" for p in sorted(a_files - b_files)]
    diffs += [f"only in fresh render: {p}" for p in sorted(b_files - a_files)]
    for rel in sorted(a_files & b_files):
        if not filecmp.cmp(a / rel, b / rel, shallow=False):
            diffs.append(f"differs: {rel}")
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render madagents/ into its Codex form.")
    parser.add_argument(
        "--check", action="store_true",
        help="render to a temp dir and fail if the tracked tree differs (for CI)",
    )
    parser.add_argument("--out", default=None, help="render somewhere else (implies no --check)")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        if args.check:
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                fresh = Path(tmp) / "madagents_codex"
                render_tree(fresh)
                diffs = dirs_differ(OUT, fresh)
            if diffs:
                print("render_codex: tracked tree is STALE:", file=sys.stderr)
                for d in diffs:
                    print(f"  {d}", file=sys.stderr)
                print("\nRe-run: python3 tools/render_codex.py", file=sys.stderr)
                return 1
            print("render_codex: tracked tree matches a fresh render")
            return 0

        out = Path(args.out).resolve() if args.out else OUT
        render_tree(out)
        n_roles = len(list((out / ".codex" / "agents").glob("*.toml")))
        n_skills = len([d for d in (out / ".agents" / "skills").iterdir() if d.is_dir()])
        print(f"render_codex: {out} — {n_roles} roles, {n_skills} skills")
        return 0
    except RenderError as exc:
        print(f"render_codex: ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
