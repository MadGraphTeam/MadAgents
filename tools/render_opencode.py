#!/usr/bin/env python3
"""Render the Claude Code agent system into its opencode form.

    python3 tools/render_opencode.py            # regenerate madagents_opencode/
    python3 tools/render_opencode.py --check    # fail if the tracked tree is stale

The sibling of ``render_codex.py``, and deliberately much thinner, because
opencode meets Claude Code most of the way:

* **Skills are copied verbatim.** opencode reads ``.claude/skills/<name>/SKILL.md``
  natively, and — unlike Codex — its frontmatter reader tolerates the
  descriptions ours actually contain. Verified: all eight load unmodified,
  including the two whose unquoted colons Codex drops silently. So there is no
  YAML normalisation step here and no divergence to police.

* **The learned tier stays where Claude Code keeps it.** An agent's slate is a
  plain ``.claude/agent-memory/<name>/MEMORY.md``, pulled into its prompt by
  ``{file:}`` interpolation. Nothing is spliced into a role file, so the
  ``codex_memory.py`` apparatus — marked regions, TOML re-parse, a bundled
  writer script, slate-preserving upgrades — has no counterpart here. That also
  means every path those cards name is **still true**, which is why the
  substitution table below is nearly empty.

What is left is the config file. opencode declares agents in
``.opencode/opencode.json``, so this renderer's real output is that one file
plus the 46 card bodies it points at.

**Runtime facts this file depends on** (all verified against opencode 1.18.11 —
see ``local/OPENCODE_NOTES.md``; re-verify before trusting them on a new
version):

1. ``.opencode/opencode.json`` is read as project config **without a git repo**.
   ``/output`` in the container is not one.
2. ``{file:...}`` paths are relative to the **config file's directory**, and
   several compose in one string.
3. ``instructions`` paths are relative to the **project root** — a different
   base in the same file. Getting this backwards fails silently: the lead simply
   starts with no instructions and nothing says so.
4. opencode defaults to allowing every permission, so the shipped ``permission``
   block is what makes the system pre-approve nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Provider-neutral helpers, imported rather than duplicated. Nothing about Codex
# comes with them; assert_safe_output takes the marker to look for as an argument
# for exactly that reason.
from render_codex import (  # noqa: E402
    RenderError,
    assert_safe_output,
    dirs_differ,
    parse_card,
    read_frontmatter,
)

sys.path.insert(0, str(REPO_ROOT / "src"))

# The empty section skeleton a cold slate carries — ma-wiki-write's "slate
# shape", so a cold agent extends a structure rather than inventing one. It is
# provider-neutral and simply happens to live in a Codex-named module; both
# renderers use this one definition rather than drifting two copies.
from launcher.codex_memory import COLD_SLATE  # noqa: E402

SRC = REPO_ROOT / "madagents"
OUT = REPO_ROOT / "madagents_opencode"
OVERRIDES = REPO_ROOT / "tools" / "opencode_overrides"
ASSETS = REPO_ROOT / "tools" / "opencode_assets"
OVERRIDE_MANIFEST = OVERRIDES / "OVERRIDES.toml"

# --------------------------------------------------------------- substitution

#: The environment description. Same role, different filename: opencode reads
#: ``AGENTS.md`` and only falls back to ``CLAUDE.md`` when there is none.
_ENV_FILE = "CLAUDE.md"
_ENV_FILE_OPENCODE = "AGENTS.md"

#: ``ma-doctor/lessons/`` is a citation corpus — agent-design principles
#: distilled from named books. Some name Claude Code because that is what the
#: cited author used; rewriting those would falsify a citation, not port a path.
_CITATION_CORPUS = ".claude/skills/ma-doctor/lessons/"


def substitute(text: str, rel: str = "") -> str:
    """Apply the path rewrites that leave a sentence true as well as well-formed.

    Exactly one rule. Every ``.claude/agent-memory/<name>/MEMORY.md`` and
    ``.claude/lead-memory/MEMORY.md`` reference is left alone **on purpose**:
    those files are at those paths on opencode too, so the cards' own sentences
    are already correct. That is the whole point of mirroring the Claude Code
    implementation rather than porting the Codex one.

    The citation corpus is exempt from even that one rule. Its entries record
    what a named author actually did — *"the author added a rule to CLAUDE.md
    after each mistake"* — and renaming the file in that sentence does not port
    a path, it falsifies a citation about a book. Exempting it from the
    assertion is not enough; it has to be exempt from the rewrite.
    """
    if rel.startswith(_CITATION_CORPUS):
        return text
    return text.replace(_ENV_FILE, _ENV_FILE_OPENCODE)


def assert_no_stale_env_file(rel: str, text: str) -> None:
    """Catch a ``CLAUDE.md`` reference that no rule and no override accounted for."""
    if rel.startswith(_CITATION_CORPUS):
        return
    if _ENV_FILE in text:
        raise RenderError(
            f"{rel}: {_ENV_FILE!r} survived rendering. Add a substitution rule, or an "
            f"override in tools/opencode_overrides/."
        )


# ------------------------------------------------------------------ overrides


def load_overrides() -> dict[str, dict]:
    if not OVERRIDE_MANIFEST.is_file():
        return {}
    return tomllib.loads(OVERRIDE_MANIFEST.read_text(encoding="utf-8")).get("override", {})


def override_for(rel: str, overrides: dict[str, dict]) -> tuple[Path, str] | None:
    """Return (override file, output relative path) for *rel*, or None.

    Verifies the SHA-256 pin first, for the reason ``render_codex.py`` spells
    out: an override is a fork, and a silently stale fork is how two providers
    drift apart.
    """
    import hashlib

    entry = overrides.get(rel)
    if entry is None:
        return None
    actual = hashlib.sha256((SRC / rel).read_bytes()).hexdigest()
    if actual != entry["sha256"]:
        raise RenderError(
            f"{rel} changed since its opencode override was written.\n"
            f"  expected sha256 {entry['sha256']}\n"
            f"  actual   sha256 {actual}\n"
            f"Re-read tools/opencode_overrides/{entry.get('renames_to', rel)}, fold in the "
            f"change, then update the sha256 in tools/opencode_overrides/OVERRIDES.toml."
        )
    path = OVERRIDES / entry.get("renames_to", rel)
    if not path.is_file():
        raise RenderError(f"{rel}: manifest names an override that does not exist: {path}")
    return path, entry.get("renames_to", rel)


# ------------------------------------------------------------------ the config

#: What the shipped system pre-approves: nothing a Claude Code run would not.
#:
#: opencode resolves an unconfigured session to ``*: allow``, so silence here
#: would mean shipping full auto-approval — the exact inverse of the Codex file,
#: where silence is the correct posture and the assertion is that nothing is
#: granted. Same invariant, opposite spelling.
#:
#: The split mirrors what Claude Code actually prompts for. ``task`` and
#: ``skill`` are allowed because dispatching a consultant and loading a skill
#: *are* the system working; making them ask would put a prompt in front of
#: every step of every run, which no Claude Code session does either.
PERMISSION = {
    "read": "allow",
    "glob": "allow",
    "grep": "allow",
    "list": "allow",
    "lsp": "allow",
    "todowrite": "allow",
    "task": "allow",
    "skill": "allow",
    "edit": "ask",
    "bash": "ask",
    "webfetch": "ask",
    "websearch": "ask",
}

#: The lead's standing context, **project-root-relative** (see the module
#: docstring, fact 3). Its discipline plus the slate it has written for itself —
#: the two things ``--append-system-prompt`` and auto-memory supply on Claude
#: Code. Session-level, so it does not leak into a consultant's prompt.
INSTRUCTIONS = [
    "prompts/lead-discipline.md",
    ".claude/lead-memory/MEMORY.md",
]

#: The lead's slate — the half of ``INSTRUCTIONS`` that has no Claude Code
#: counterpart in ``append_system_prompt_file`` (there it arrives through
#: auto-memory instead), so it is excluded when the two are compared.
_LEAD_SLATE_ENTRY = ".claude/lead-memory/MEMORY.md"


def assert_instructions_match_canonical() -> None:
    """Fail if the canonical preset's prompt files are not what we emit.

    ``INSTRUCTIONS`` is written out by hand because the two keys resolve against
    different roots and only this renderer knows that. The cost is that it can
    drift from ``config.yaml``'s ``append_system_prompt_file``, which is the
    canonical statement of what the lead starts with — and ``resolve_system_prompt``
    accepts a *list*, so adding a second prompt file there would leave the
    opencode lead silently missing it. A rename fails loudly on its own (the copy
    below would not find the file); an addition would not. Hence this check.
    """
    import yaml

    data = yaml.safe_load((SRC / "config.yaml").read_text(encoding="utf-8")) or {}
    declared = data.get("append_system_prompt_file")
    if not declared:
        raise RenderError(
            f"{SRC / 'config.yaml'}: append_system_prompt_file is empty, so the canonical "
            f"preset states no lead prompt — but this renderer emits {INSTRUCTIONS}."
        )
    if isinstance(declared, str):
        declared = [declared]
    # config.yaml states repo-relative paths ("madagents/prompts/…"); the
    # rendered tree states project-root-relative ones ("prompts/…").
    want = [p.split("/", 1)[1] if p.startswith(f"{SRC.name}/") else p for p in declared]
    got = [i for i in INSTRUCTIONS if i != _LEAD_SLATE_ENTRY]
    if want != got:
        raise RenderError(
            f"the canonical preset's lead prompt files {want} do not match what this renderer "
            f"puts in opencode.json's `instructions` ({got}). Update INSTRUCTIONS in "
            f"tools/render_opencode.py — and remember the two keys resolve against different "
            f"roots: `instructions` from the PROJECT ROOT, `{{file:}}` from the config's dir."
        )

#: Card body and slate, composed into one prompt. **Config-dir-relative**
#: (fact 2), i.e. resolved from ``.opencode/``.
_CARD_REF = "{{file:./cards/{name}.md}}"
_SLATE_REF = "{{file:../.claude/agent-memory/{name}/MEMORY.md}}"

#: Keys that must never appear in the tracked config: they are the endpoint and
#: its credential, which the instance builder writes at build time from
#: local/config.env. See the plan's §B3a and .gitignore.
_FORBIDDEN_TOP_LEVEL = ("provider", "model", "small_model")
_FORBIDDEN_ANYWHERE = ("apiKey", "baseURL")


def build_config(cards: list[Path], overrides: dict[str, dict]) -> tuple[dict, list[str]]:
    """Assemble ``opencode.json`` from the 46 cards.

    Returns the config and the names that carry a learned tier, so the caller
    can lay down the cold slate files those prompts reference.
    """
    agents: dict[str, dict] = {}
    slate_names: list[str] = []
    for card in sorted(cards):
        rel = f".claude/agents/{card.name}"
        fields, _ = parse_card(card)
        name = fields["name"]
        description = " ".join(substitute(fields["description"], rel).split())
        assert_no_stale_env_file(rel, description)
        prompt = _CARD_REF.format(name=name)
        # The five reviewer/auditor cards carry no `memory:` — they are
        # dispatched fresh every time and hold no learned tier, so they get no
        # slate reference. Pointing at a file that will never exist would be
        # harmless but dishonest.
        if fields.get("memory"):
            prompt += "\n\n" + _SLATE_REF.format(name=name)
            slate_names.append(name)
        agents[name] = {
            "description": description,
            "mode": "subagent",
            "prompt": prompt,
        }
    config = {
        "$schema": "https://opencode.ai/config.json",
        "instructions": list(INSTRUCTIONS),
        "permission": dict(PERMISSION),
        "agent": agents,
    }
    return config, slate_names


def check_config(config: dict) -> None:
    """Assert the shipped config says what it looks like it says."""
    missing = set(PERMISSION) - set(config.get("permission", {}))
    if missing or not config.get("permission"):
        raise RenderError(
            f"opencode.json is missing permission keys {sorted(missing)}. opencode defaults "
            f"every permission to 'allow', so an absent or partial block ships a system that "
            f"pre-approves everything — the Claude Code side pre-approves nothing."
        )
    present = [k for k in _FORBIDDEN_TOP_LEVEL if k in config]
    if present:
        raise RenderError(
            f"opencode.json contains {present}. The tracked tree describes the agent system "
            f"only; the endpoint and its credential are written into the run instance at "
            f"build time (run_dir/ is gitignored). Never commit them."
        )
    blob = json.dumps(config)
    leaked = [k for k in _FORBIDDEN_ANYWHERE if k in blob]
    if leaked:
        raise RenderError(
            f"opencode.json contains {leaked} somewhere in its body. A credential or endpoint "
            f"must not reach the tracked tree."
        )


# ---------------------------------------------------------------------- render


def render_tree(out: Path) -> None:
    # Preconditions FIRST — before the rmtree below. A check that runs after the
    # output tree has been wiped turns a caught mistake into a half-rendered tree
    # that `--check` then reports as merely 'stale', which is a far more confusing
    # thing to hand someone than a clean refusal.
    assert_safe_output(out, ".opencode/cards")
    assert_instructions_match_canonical()
    overrides = load_overrides()
    used: set[str] = set()

    if out.exists():
        shutil.rmtree(out)
    (out / ".opencode" / "cards").mkdir(parents=True)
    (out / ".claude" / "skills").mkdir(parents=True)
    (out / "prompts").mkdir()

    # --- cards: bodies only. The frontmatter's job is done by opencode.json.
    cards = sorted((SRC / ".claude" / "agents").glob("*.md"))
    if not cards:
        raise RenderError(f"no cards found in {SRC / '.claude' / 'agents'}")
    for card in cards:
        rel = f".claude/agents/{card.name}"
        over = override_for(rel, overrides)
        if over is not None:
            used.add(rel)
            body = over[0].read_text(encoding="utf-8")
        else:
            _, body = parse_card(card)
            body = substitute(body, rel)
            assert_no_stale_env_file(rel, body)
        (out / ".opencode" / "cards" / f"{card.stem}.md").write_text(body + "\n", encoding="utf-8")

    config, slate_names = build_config(cards, overrides)
    check_config(config)
    (out / ".opencode" / "opencode.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )

    # --- cold slates.
    #
    # A `{file:}` reference to a file that does not exist is a HARD error on
    # opencode — "Configuration is invalid … bad file reference" — and opencode
    # refuses the whole config, so a cold run comes up with **zero** consultants.
    # Shipping the empty skeleton is the same answer render_codex.py gives by
    # baking COLD_SLATE into every role file, and it costs nothing: a memory
    # pack simply overwrites these on its way in.
    #
    # `instructions` is the opposite — a missing file there is skipped silently.
    # That is why the lead gets no skeleton: absent genuinely means cold, and
    # an empty one would only put four blank headings in its context.
    for name in slate_names:
        slate = out / ".claude" / "agent-memory" / name / "MEMORY.md"
        slate.parent.mkdir(parents=True, exist_ok=True)
        slate.write_text(COLD_SLATE, encoding="utf-8")

    # --- skills: verbatim, because opencode reads this tree as-is.
    skills_src = SRC / ".claude" / "skills"
    for src_file in sorted(skills_src.rglob("*")):
        if src_file.is_dir():
            continue
        rel = f".claude/skills/{src_file.relative_to(skills_src)}"
        over = override_for(rel, overrides)
        if over is not None:
            used.add(rel)
            override_path, renamed = over
            dest = out / ".claude" / "skills" / Path(renamed).relative_to(".claude/skills")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(override_path.read_text(encoding="utf-8"), encoding="utf-8")
            continue
        dest = out / ".claude" / "skills" / src_file.relative_to(skills_src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src_file.suffix == ".md":
            text = substitute(src_file.read_text(encoding="utf-8"), rel)
            assert_no_stale_env_file(rel, text)
            dest.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src_file, dest)

    # --- the lead's slate, mirrored from the canonical preset.
    #
    # madagents/ ships `.claude/lead-memory/MEMORY.md` as an EMPTY file: the
    # lead has learned nothing yet, but the file and its directory exist so its
    # first /ma-wiki-write has somewhere to write. Copied rather than
    # re-created, so whatever the canonical preset decides to ship there
    # arrives here too.
    #
    # (An empty file in `instructions` contributes nothing, and a missing one
    # is skipped silently — so unlike the consultant slates this is about the
    # write path, not the read path.)
    lead_mem_src = SRC / ".claude" / "lead-memory"
    if lead_mem_src.is_dir():
        for src_file in sorted(lead_mem_src.rglob("*")):
            if src_file.is_dir():
                continue
            dest = out / ".claude" / "lead-memory" / src_file.relative_to(lead_mem_src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest)
    else:
        (out / ".claude" / "lead-memory").mkdir(parents=True, exist_ok=True)

    # --- slash commands, one per skill.
    #
    # On Claude Code a skill IS a slash command: the system's own prose says
    # "/mg-probe" (51 times), "/mg-deep-verify" (87), "/mg-study" (46), and the
    # README tells users they can invoke any skill by name. opencode does not
    # work that way — skills are reached through its `skill` tool, and slash
    # commands are a separate surface (`.opencode/command/<name>.md`). Without
    # these, every one of those instructions names something that does not
    # exist, for the user and the lead alike.
    #
    # The command is a thin shim onto the skill, so the skill body stays the
    # single source of truth and cannot drift from its own launcher.
    commands = out / ".opencode" / "command"
    commands.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(p for p in (out / ".claude" / "skills").iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        fields = read_frontmatter(
            re.match(r"^---\n(.*?)\n---\n", skill_md.read_text(encoding="utf-8"), re.S).group(1),
            str(skill_md),
        )
        name = fields.get("name") or skill_dir.name
        description = " ".join(fields.get("description", "").split())
        (commands / f"{name}.md").write_text(
            "---\n"
            f"description: {json.dumps(description)}\n"
            "---\n"
            f"Load the `{name}` skill with the skill tool, then carry it out for the "
            f"request below. Follow the skill's own procedure; do not improvise a "
            f"substitute for it.\n\n"
            "$ARGUMENTS\n",
            encoding="utf-8",
        )

    # --- the lead's instructions (a real file at the project root, as on
    #     Claude Code — only the delivery mechanism differs)
    lead_src = SRC / "prompts" / "lead-discipline.md"
    lead_text = substitute(lead_src.read_text(encoding="utf-8"), "prompts/lead-discipline.md")
    assert_no_stale_env_file("prompts/lead-discipline.md", lead_text)
    (out / "prompts" / "lead-discipline.md").write_text(lead_text, encoding="utf-8")

    # --- static assets
    for asset, dest_rel in (("config.yaml", "config.yaml"), ("AGENTS.md.seed", "AGENTS.md.seed")):
        (out / dest_rel).write_text((ASSETS / asset).read_text(encoding="utf-8"), encoding="utf-8")

    unused = sorted(set(overrides) - used)
    if unused:
        raise RenderError(
            f"override manifest names files that were never rendered: {unused}. "
            f"Remove the entry, or fix the path."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render madagents/ into its opencode form.")
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
                fresh = Path(tmp) / "madagents_opencode"
                render_tree(fresh)
                diffs = dirs_differ(OUT, fresh)
            if diffs:
                print("render_opencode: tracked tree is STALE:", file=sys.stderr)
                for d in diffs:
                    print(f"  {d}", file=sys.stderr)
                print("\nRe-run: python3 tools/render_opencode.py", file=sys.stderr)
                return 1
            print("render_opencode: tracked tree matches a fresh render")
            return 0

        out = Path(args.out).resolve() if args.out else OUT
        render_tree(out)
        config = json.loads((out / ".opencode" / "opencode.json").read_text())
        n_skills = len([d for d in (out / ".claude" / "skills").iterdir() if d.is_dir()])
        print(f"render_opencode: {out} — {len(config['agent'])} agents, {n_skills} skills")
        return 0
    except RenderError as exc:
        print(f"render_opencode: ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
