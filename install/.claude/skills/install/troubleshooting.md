# When an install goes wrong

Failure modes in the order they actually happen. Diagnose before you act — most of
these look identical from the outside ("it forgot everything") and have different causes.

## The session came up cold — none of the memory loaded

Two causes. Check them in this order.

**1. The folder is not its own git root.** Claude Code resolves a project root to the
enclosing git repository, and the roster's `memory: project` agents read their slates
relative to that root. An install inside another repo, made with `--no-git`, loads its
slates from *that* repo's `.claude/` — which has none.

```bash
git -C <target> rev-parse --show-toplevel
```

If that prints anything other than `<target>`, it is the bug. Fix:

```bash
git init <target>
```

A nested repo is correct here and is exactly what the container path does for its
`output/`. `--no-git` is only right when the folder already *is* a repository root.

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

## There is already an install here

`installer.py` refuses rather than overwrite:

```
ERROR: /home/you/my-study/.claude already exists
  Use --upgrade to refresh the agent system there, or pick another folder.
```

That refusal is protecting the learned tier — a fresh install would discard everything
the sessions in that folder worked out. Offer `--upgrade` (replaces the shipped system,
keeps the tier, the wiki, `CLAUDE.md`) and never talk the user out of the refusal to
save a step. `--upgrade` rejects `--memory` for the same reason: changing the starting
memory of an install that already has its own is not an upgrade, it is a new install.

## Unknown memory pack

```
ERROR: no memory pack named 'typo' in /path/to/MadAgents/memory
       Available: bare-local, pretrained, pretrained-local — or 'none' to start cold.
```

Run `python3 installer.py --list-memory` and put the choice to the user again. A pack
is a directory under `memory/` containing a `.claude/`; nothing else counts as one.

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
