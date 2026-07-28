# Installing MadAgents without a container

`./madrun.sh` runs MadAgents inside Apptainer, on an image that already has
MadGraph. This folder is the other case: putting the agent system **into a folder
on your own machine**, to run against a MadGraph you already have — or none at all.

Start a Claude Code session in this folder and it installs for you — it asks where,
and which memory pack:

```bash
cd install && claude
```

There is no wrapper script; the session picks the installer up from `install/.claude/`.
To skip the conversation entirely, call the installer directly from the repo root:

```bash
python3 install/installer.py ~/my-study --memory pretrained
```

Then:

```bash
cd ~/my-study && ./madagents.sh
```

## The two paths, side by side

| | `./madrun.sh` | an install |
| --- | --- | --- |
| Needs Apptainer | yes | no |
| MadGraph | ships in the image | yours, wherever it is |
| Where it runs | a container, one run per instance | any folder, as many as you like |
| Deliverables | `<instance>/output/` | the folder itself |
| Isolation | container + per-run overlay | none — it is your filesystem |

The agent system is identical in both. What differs is everything around it.

> **No sandbox.** A run instance is contained: the agent works in an overlay that
> starts fresh, and `/output` is the only thing it can hand you. An install has none
> of that — the session runs as you, in your filesystem, with your permissions. That
> is the point of it, and the reason to keep the default permission prompts on until
> you know what a given task will do.

## What gets installed

```
<target>/
  .claude/            46 consultant agents, 8 skills, the learned tier, settings
  .madagents/wiki/    the wiki half of the learned tier
  prompts/            the lead's system prompt
  config.yaml         the configuration this install was built from
  CLAUDE.md           environment description — the session's to maintain
  madagents.sh        start a session here
  memory-pack.txt     which pack seeded this install
```

The target becomes a git repository (a nested one, if it sits inside another). That
is not for version control: Claude Code resolves a project root to the enclosing git
repo, and the roster's per-agent memory is read and written relative to that root. An
install that is not its own root would load its slates from somewhere else. `--no-git`
skips it, and is correct only when the folder is already a repository root.

## Memory packs

The same packs `./madrun.sh` offers, seeded the same way — copied in, so the install
extends its own copy and `memory/<pack>/` stays fixed.

```bash
python3 install/installer.py --list-memory
```

See [`../memory/README.md`](../memory/README.md). Pick `pretrained` unless you are
running a self-hosted model (`pretrained-local`, `bare-local`) or want an empty
learned tier (`none`).

## MadGraph

An install cannot bring one. The container knows where MadGraph is because its image
put it there; on your machine it is wherever you have it, and the installer will not
guess. So the seeded `CLAUDE.md` says the location is unrecorded and asks the session
to write it down once it knows:

```markdown
- MadGraph: not recorded. Find it, then replace this line with its path.
```

Fill that line in yourself if you like. Either way the file is the session's from
then on — it is expected to correct and extend it as it learns the filesystem, and
nothing overwrites it afterwards.

## Upgrading

```bash
python3 install/installer.py ~/my-study --upgrade
```

Replaces the shipped agent system — `agents/`, `skills/`, `prompts/`, `config.yaml`,
and the wrapper — and leaves everything the sessions there produced: the learned
tier, the wiki, `CLAUDE.md`, your files. Installing over an existing install without
`--upgrade` is refused rather than silently discarding that.

## Moving an install

Just move the folder. Claude Code needs an absolute path for the memory directory, so
`madagents.sh` re-points it on every start; a moved install says so once and carries
on.

## Starting it

`./madagents.sh` — which is `claude` in that folder, plus the lead's system prompt and
the model settings from `config.yaml`. Arguments are forwarded, so `--resume`,
`--continue` and friends work as usual. A bare `claude` there is not the same thing:
it picks up the roster, the skills, the memory and `CLAUDE.md`, but not the system
prompt that tells the lead how to conduct them.
