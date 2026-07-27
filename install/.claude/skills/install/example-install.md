# A finished install, in full

What `installer.py` produces, so you can check a result and explain it without reading
the script. This is a `--memory pretrained` install into `~/my-study`.

## What it prints

```
madagents install: installing 'madagents' → /home/you/my-study
madagents install: 46 agents, 8 skills, memory pretrained (46 slates, 592 wiki pages)
madagents install: start it with  cd /home/you/my-study && ./madagents.sh
```

Three numbers are worth reading back to the user, because they are the ones that can
come out wrong: **agents** and **skills** say the system copied; **slates** and **wiki
pages** say the memory seeded. A `pretrained` install that reports `0 slates` did not
seed — do not report success. A `--memory none` install reporting `0 slates, 0 wiki
pages` is correct and expected.

## The tree

```
~/my-study/
  .claude/
    agents/            46 consultant subagents
    skills/            8 skills (mg-setup, mg-probe, ma-wiki-write, …)
    agent-memory/      46 per-consultant slates      ┐ the learned tier,
    lead-memory/       the lead's slate + playbooks   │ from the memory pack
    settings.local.json
  .madagents/wiki/     592 pages, consultants/ + lead/  ┘
  prompts/
    lead-discipline.md the lead's system prompt
  config.yaml          the configuration this install was built from
  CLAUDE.md            environment description — the session's to maintain
  madagents.sh         start a session here
  memory-pack.txt      provenance of the learned tier
  .git/                makes this folder its own Claude Code project root
```

## The generated files

**`madagents.sh`** — the launcher's job, reduced to what applies without a container.
Everything Claude Code can discover from a directory is left to it; what it cannot is
baked in here:

```bash
[[ -f "prompts/lead-discipline.md" ]] || { echo "ERROR: … missing — reinstall." >&2; exit 1; }

# … re-points auto-memory if the folder moved (see troubleshooting.md) …

exec claude --append-system-prompt "$(cat -- "prompts/lead-discipline.md")" "$@"
```

`--model` and `--effort` are appended too, but only when `config.yaml` sets them; the
shipped configuration leaves both null, so a normal install has neither.

**`.claude/settings.local.json`** — two keys, both load-bearing:

```json
{
  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "/home/you/my-study/.claude/lead-memory"
}
```

`autoMemoryEnabled` is written explicitly because Claude Code merges it over the
user's own settings — someone who turned auto-memory off globally would otherwise get
an install whose 46 slates never load. `autoMemoryDirectory` must be absolute, which
is why the wrapper re-points it when the folder moves.

**`CLAUDE.md`** — seeded, then the session's:

```markdown
# Environment

- `.` — project root; you start here. Wiki: `.madagents/wiki/`.
- MadGraph: not recorded. Find it, then replace this line with its path.

Keep this file current — filesystem facts only.
```

Leave the MadGraph line alone unless the user tells you the path. It is not a gap to
be filled in on their behalf — the first session finds out and records it.

**`memory-pack.txt`** — which pack seeded this install, and that the pack itself was
not touched:

```
pretrained
# Seeded by install/installer.py from /path/to/MadAgents/memory/pretrained.
# This install owns its copy; the pack is unchanged. See memory/README.md.
```

## An upgrade, for contrast

```
madagents install: upgrading 'madagents' → /home/you/my-study
madagents install: agent system replaced (46 agents, 8 skills); learned tier untouched
madagents install: start it with  cd /home/you/my-study && ./madagents.sh
```

`agents/`, `skills/`, `prompts/`, `config.yaml` and the wrapper are replaced.
`agent-memory/`, `lead-memory/`, `.madagents/`, `CLAUDE.md`, `memory-pack.txt` and the
user's own files are not — which is why the line says *learned tier untouched*, and why
an upgrade reports no slate or page counts: it did not seed any.
