# When an install goes wrong

Failure modes in the order they actually happen. Diagnose before you act — most of
these look identical from the outside ("it forgot everything") and have different causes.

## The session came up cold — none of the memory loaded

Two causes. Check them in this order.

**1. The folder is not its own git root.** Claude Code resolves a project root to the
enclosing git repository, and the roster's `memory: project` agents read their slates
relative to that root. An install inside another repo loads its slates from *that*
repo's `.claude/` — which has none.

```bash
git -C <target> rev-parse --show-toplevel
```

If that prints anything other than `<target>`, it is the cause. Two fixes, and which
one is right depends on whose folder it is:

- **The folder is theirs to use this way** — `git init <target>`. A nested repo is
  exactly what the container path does for its `output/`.
- **The install is additive, inside a repo they work in** — leave the repo alone and
  pin `autoMemoryDirectory` to an absolute path inside the install instead. Never
  `git init` somebody's subdirectory to fix a memory path.

A Codex install has neither problem: each consultant's slate travels inside its own
role file, so there is no project-root-relative lookup to get wrong.

**2. The settings do not point here.** `<target>/.claude/settings.local.json` must
carry `autoMemoryEnabled: true` and an `autoMemoryDirectory` that is this folder's
`.claude/lead-memory` — absolute. If it names some other path, see the next section.

Then confirm the tier is actually populated: `ls <target>/.claude/agent-memory | wc -l`
should be 46 for a `pretrained` install. Zero means the seed did not happen, not that
loading failed — reinstall into a fresh folder.

## The folder was moved and the memory went with it — but did not load

`autoMemoryDirectory` is an absolute path, so moving the folder invalidates it.
`madagents.sh` re-points it on every start, printing one line when it does:

```
madagents: this folder moved — auto-memory re-pointed at /new/path/.claude/lead-memory
```

That step needs `python3` on `PATH`. Without it the wrapper skips silently and the
session comes up cold. Either put `python3` on `PATH`, or fix the one key by hand:

```json
"autoMemoryDirectory": "/new/path/.claude/lead-memory"
```

## There is already something here

Read `<target>/.madagents/install.json`. It is the only evidence that decides this:

- **Manifest present** → an existing install. Upgrade it: replace exactly the `paths`
  it records and keep the learned tier. Never re-install fresh over it to save a step —
  that discards everything the sessions in that folder worked out.
- **No manifest, but files present** → the user's own project. This is an *additive*
  install, and every collision gets named before anything is written.

**A `.claude/` or `.codex/` directory is not evidence of an install.** Every project
anyone has ever run either CLI in has one. The old installer treated it as proof, and
its `--upgrade` then `rmtree`d `.claude/agents` and `.claude/skills` — taking the host
project's own agents and skills with it. That is the failure this whole design exists
to make impossible; do not reintroduce it by reasoning from a directory listing.

## `verify` reports something

```bash
python3 installer.py verify <target>
```

- `FAIL … role file(s) do not parse as TOML` — those consultants do not exist and
  never will; nothing else reports it. Re-copy them from the shipped tree.
- `FAIL … skill(s) have unreadable frontmatter` — usually an unquoted `": "` in
  `description:`. Codex drops such a skill silently; Claude Code tolerates it, so the
  same install can be fine on one provider and quietly short a skill on the other.
- `FAIL … pre-existing file(s) were OVERWRITTEN/REMOVED` — the install damaged
  something the user already had. Restore it before reporting anything else.
- `skip  no pre-install baseline recorded` — the most important check did not run. The
  install is *unproven*, not proven good; say so rather than reporting a pass.
- `warn … not recorded as trusted` (Codex) — answer yes on the first `codex` run in the
  folder, or `.codex/` is ignored entirely and the roster silently does not exist.

## Unknown memory pack

A pack is a directory under `memory/` containing a `.claude/`; nothing else counts. List
the real ones and put the choice to the user again:

```bash
python3 -c "import sys; sys.path.insert(0,'../src'); from launcher.setup import memory_options; [print(n, '-', d) for n, d in memory_options()]"
```

## The user has no MadGraph on this machine

Say so plainly rather than installing and letting them find out. The agent system
installs and runs fine — routing, the roster, the skills, the wiki — but everything it
exists to do against a real MadGraph (probing a setup, walking source, running a
process) needs one. Their options are to install MadGraph themselves, or to use the
container path (`./madrun.sh`), which brings its own. Neither is your call to make for
them; put both and let them choose.

## It behaves like plain Claude Code

Started with a bare `claude` instead of `./madagents.sh`. A bare start still picks up
the roster, the skills, the memory and `CLAUDE.md` — everything that lives in the
directory — but not the appended system prompt that tells the lead how to conduct them.
The symptom is a session that answers directly instead of dispatching consultants.

## MadGraph is installed, but the session keeps rediscovering it

The path was never written down. `CLAUDE.md` is the only place that survives a session,
and it is the session's to maintain — check that the MadGraph line was actually updated
rather than left at `not recorded`. If the user tells you the path, offer to write that
one line. Do not add anything else to the file: it is a filesystem description, not a
notes file.
