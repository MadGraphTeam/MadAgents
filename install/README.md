# Installing MadAgents without a container

`./madrun.sh` runs MadAgents inside Apptainer, on an image that already has
MadGraph. This folder is the other case: putting the agent system **into a folder
on your own machine**, to run against a MadGraph you already have — or none at all.

Start a session in this folder with **either CLI** and it installs for you — it asks
where, which memory pack, and which CLI to install *for*:

```bash
cd install && claude     # picks the installer up from install/.claude/
cd install && codex      # picks it up from install/.agents/ + AGENTS.md
```

The two are independent choices. Whichever you run, you can install either system:
a Codex user can build a Claude Code install and vice versa.

There is no wrapper script, and **no installer script**. The session does the install
itself, working to the contract in [`install-policy.md`](install-policy.md), and then
verifies it:

```bash
python3 install/installer.py verify ~/my-study
```

That is all `installer.py` does now — it is read-only. It used to do the install, and
that was the bug: a script cannot tell a MadAgents install from your own project, so it
guessed (`.claude/` exists), and its `--upgrade` deleted the host project's own agents
and skills. An agent can look at the folder and ask.

> **Installing into a repository you already work in** is now a supported case rather
> than a hazard. The session surveys the folder, names every collision before writing,
> and never removes a path it did not install.

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

With `--provider codex`, the same system laid out the way Codex looks for it:

```
<target>/
  .codex/agents/      46 role files — each one a consultant's card AND its slate
  .codex/config.toml  deliberately empty — it explains what is NOT set, and why
  .agents/skills/     8 skills (+ ma-wiki-write/scripts/write_slate.py)
  .madagents/         wiki/ , and memory/lead/MEMORY.md — the lead's slate
  prompts/            the lead's instructions
  AGENTS.md           environment description — the session's to maintain
  madagents.sh        start a session here
```

A consultant's slate is inside its role file because that file is what Codex auto-loads
on every dispatch of that role. It is written through `write_slate.py`, never by hand:
a malformed role file is dropped from the roster with no error, which would take the
consultant's card down along with everything it had learned.

**First run on Codex:** it asks whether to trust the folder. Answer yes — untrusted, Codex
ignores `.codex/` entirely and the consultants silently do not exist. `/agent` tells you
which roles are live.

**git.** On Claude Code, the roster's per-agent memory is read and written relative to
the enclosing git repository, so an install that is not its own root loads its slates
from somewhere else. The session explains that and lets you choose: `git init` the
folder, or leave your repo alone and pin `autoMemoryDirectory` to an absolute path
inside the install. It will not `git init` a folder of yours without asking. A Codex
install has neither problem — each consultant's slate travels inside its own role file.

## Memory packs

The same packs `./madrun.sh` offers, seeded the same way — copied in, so the install
extends its own copy and `memory/<pack>/` stays fixed. The session lists them and asks,
so there is nothing to pass.

See [`../memory/README.md`](../memory/README.md). Pick `pretrained` unless you are
running a self-hosted model (`pretrained-local-cc`, `bare-local-cc`) or want an empty
learned tier (`none`).

> The `-opencode` packs are listed too, because the list comes from `memory/`. They do
> not belong in an install: an install is a `claude_code` or a `codex` one, and opencode
> is reached through `./local/madrun.sh`. Seeding one here states the wrong harness
> mechanic to the lead, which nothing detects for you.

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

Start a session in `install/` again and point it at the folder. It reads the
manifest — `.madagents/install.json`, written at install time — and replaces exactly
the paths recorded there: the roster, the skills, `prompts/`, `config.yaml` and the
wrapper. Everything the sessions produced is left alone: the learned tier, the wiki,
`CLAUDE.md` / `AGENTS.md`, and your own files.

The manifest is also what makes "is there already an install here?" a fact rather than
a guess. It has to be, because the guess it replaced — *does `.claude/` exist?* — is
true of every folder anyone has ever run Claude Code in.

On Codex the roster cannot simply be overwritten, since each role file holds a
consultant's card *and* its slate. The upgrade replaces the card half and splices the
existing slate back into it, so a release can change how a consultant works without
discarding what it learned. A role the new release no longer ships is removed and its
slate goes with it — the installer says so rather than dropping it quietly.

The provider comes from the manifest, not from a flag: a Codex install is always
upgraded as a Codex install. There is no conversion between the two learned tiers.

## Moving an install

Just move the folder. Claude Code needs an absolute path for the memory directory, so
`madagents.sh` re-points it on every start; a moved install says so once and carries
on. A Codex install has no absolute path to re-point — each consultant's slate travels
inside the role file, and the lead's is found relative to the folder — so it simply
moves.

## Starting it

`./madagents.sh` — which is `claude` in that folder, plus the lead's system prompt.
Arguments are forwarded, so `--resume`, `--continue`, `--model` and friends work as
usual; the model is yours to pick, exactly as in any other session. A bare `claude`
there is not the same thing:
it picks up the roster, the skills, the memory and `CLAUDE.md`, but not the system
prompt that tells the lead how to conduct them.

On Codex it is `codex` in that folder, plus the same one thing — the lead's
instructions (its shipped discipline *and* the slate it has written for itself).
The same caveat applies, and a little more sharply: Codex's own guidance
tells a session to delegate only when asked, so a bare `codex` there has the roster but
not the instruction to use it.
