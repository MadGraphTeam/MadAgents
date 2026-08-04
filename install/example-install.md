# A finished install, in full

What a finished install looks like, so you can check a result and explain it. Shared by
both installer agents — the artifact is the same whichever CLI built it. This is a
`pretrained` install into `~/my-study`.

## The tree — Claude Code

```
~/my-study/
  .claude/
    agents/            46 consultant subagents
    skills/            8 skills (mg-setup, mg-probe, ma-wiki-write, …)
    agent-memory/      46 per-consultant slates      ┐ the learned tier,
    lead-memory/       the lead's slate + playbooks   │ from the memory pack
    settings.local.json
  .madagents/
    wiki/              592 pages, consultants/ + lead/  ┘
    install.json       the manifest — what this install owns
  prompts/
    lead-discipline.md the lead's system prompt
  config.yaml          the configuration this install was built from
  CLAUDE.md            environment description — the session's to maintain
  madagents.sh         start a session here
  memory-pack.txt      provenance of the learned tier
```

## The tree — Codex

Same system, the layout Codex reads. Note where the learned tier goes:

```
~/my-study/
  .codex/
    agents/            46 consultant ROLES — each carries its own slate inside it
    config.toml
  .agents/skills/      8 skills
  .madagents/
    memory/lead/       the lead's slate  (consultants' are in the role files)
    wiki/              592 pages
    install.json
  prompts/
    lead-discipline.md
    lead-slate-header.md   the wrapper concatenates the lead's slate under this
  config.yaml
  AGENTS.md            environment description
  madagents.sh
  memory-pack.txt
```

There is **no `agent-memory/` on Codex, and no `settings.local.json`** — both are
absent by design, not missing. A consultant's slate travels inside its role file, which
is also why a Codex install is relocatable and a Claude Code one is not.

## What to read back to the user

Counts are what can come out wrong:

- **46 agents / roles** and **8 skills** say the system copied.
- **slates** and **wiki pages** say the memory seeded. A `pretrained` install with
  0 slates did not seed — do not report success. A `none` install with 0 of both is
  correct.
- On Codex, count *populated* slates inside the role files
  (`codex_memory.count_seeded`), not files in a directory.

## The manifest — `.madagents/install.json`

The one file that makes the folder identifiable as an install, and the input to every
later upgrade and every verify:

```json
{
  "schema": 1,
  "provider": "claude_code",
  "memory_pack": "pretrained",
  "installed_at": "2026-08-03T11:20:00Z",
  "prompt_files": ["prompts/lead-discipline.md"],
  "disallowed_tools": [],
  "paths": {".claude/agents/mg-syntax.md": "3f7a…", "…": "…"},
  "generated": ["madagents.sh", ".claude/settings.local.json", "CLAUDE.md",
                "memory-pack.txt", ".madagents/install.json"],
  "preexisting": {}
}
```

`preexisting` is empty here because the folder was empty. On an additive install it
holds a hash of every file that was already there — the baseline that lets `verify`
prove nothing of the user's was clobbered. **Empty and absent are different**: absent
means the baseline was never taken and that check cannot run.

## The wrapper

Produced by substituting the two placeholder lines in `install/templates/madagents.sh` —
nothing else in it is written by hand, which is why `verify` can re-render the template
and compare byte-for-byte.

```bash
PROMPT_FILES=(
  "prompts/lead-discipline.md"
)
DISALLOWED_TOOLS=(
)
…
exec claude "${FLAGS[@]}" "$@"
```

It pins no model and no reasoning effort — an install starts an interactive session, so
those stay the operator's to pick, in-session or by forwarding a flag
(`./madagents.sh --model <id>`).

The Codex wrapper is the same idea against `templates/madagents-codex.sh`: it builds
`developer_instructions` from the prompt files, then appends the lead's slate under
`prompts/lead-slate-header.md` if one has been written.

## `.claude/settings.local.json` — Claude Code only

```json
{
  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "/home/you/my-study/.claude/lead-memory"
}
```

`autoMemoryEnabled` is written explicitly because Claude Code merges it over the user's
own settings — someone who turned auto-memory off globally would otherwise get an
install whose 46 slates never load. `autoMemoryDirectory` must be absolute, which is why
the wrapper re-points it when the folder moves.

**If the user already had this file, these two keys are merged into it.** It is never
replaced.

## The environment description

```markdown
# Environment

- `.` — project root; you start here. Wiki: `.madagents/wiki/`.
- MadGraph: not recorded. Find it, then replace this line with its path.

Keep this file current — filesystem facts only.
```

Seeded **only when there is none**. Leave the MadGraph line alone unless the user tells
you the path — it is not a gap to fill in on their behalf; the first session finds out
and records it.

## `memory-pack.txt`

```
pretrained
# This install owns its copy; the pack is unchanged. See memory/README.md.
```

## An upgrade, for contrast

Replaced: everything in the manifest's `paths` — the roster, the skills, `prompts/`,
`config.yaml`, and the wrapper.

Untouched: `agent-memory/`, `lead-memory/`, `.madagents/memory/`, `.madagents/wiki/`,
`CLAUDE.md` / `AGENTS.md`, `memory-pack.txt`, and everything of the user's own.

On Codex the roster is the interesting case: a role file is card *and* slate at once, so
each one is replaced by reading the slate out, copying the new card in, and writing the
slate back — never by overwriting the file. A role the new release no longer ships is
removed, and its slate goes with it; say so out loud when it happens.
