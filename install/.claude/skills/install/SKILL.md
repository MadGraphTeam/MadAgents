---
name: install
description: Install the MadAgents agent system into a folder on this machine, to be run without a container. Use when the user wants MadAgents outside Apptainer — in a project folder, on a login node, or anywhere they already have MadGraph — or wants to refresh an existing install.
---

# Install MadAgents into a folder

Your working directory is `install/`, so every command below is run from there.

Beside this file, read on demand:

- `example-install.md` — a finished install in full: the tree, the generated wrapper and
  settings, the seeded `CLAUDE.md`, and what the installer prints. Open it to check a
  result, or to explain to the user what just landed in their folder.
- `troubleshooting.md` — the failure modes and how to tell them apart. Open it the
  moment something is off; several of them look identical from the outside.

## 1. Ask both questions before doing anything

**Where.** The folder to install into. It becomes the session's project root, so it
should be the folder the user will actually work in — a study directory, not a
throwaway. Accept `~`; the installer resolves it. If they name an existing folder,
say what you find in it before writing anything.

**Which memory pack.** Run `python3 installer.py --list-memory` and show the user the
list with its descriptions. Do not summarise the packs from memory — the descriptions
ship with the packs and are the current ones. If they have no preference: `pretrained`
is the default and the right answer for Anthropic models; the two `-local` packs are
for a self-hosted model; `none` starts with an empty learned tier.

Ask both, then confirm the pair back before running.

## 2. Check the target

- `<target>/.claude` exists → this is already an install. Offer `--upgrade`, which
  replaces the agents, skills, prompts and config while keeping the learned tier,
  `CLAUDE.md` and the memory pack. Never re-install over it without saying so — a
  fresh install would discard everything the sessions there learned.
- The folder is inside another git repository → the installer nests a repo so Claude
  Code resolves the project root to the install itself. Mention it; some users would
  rather pick a folder outside their repo. `--no-git` skips it, and is only correct
  when the folder is already its own repository root.

## 3. Run it

```bash
python3 installer.py <target> --memory <pack>
python3 installer.py <target> --upgrade        # refresh, keep the learned tier
```

That is the whole installation. Do not copy files yourself, do not fix up what it
wrote, and do not edit the generated `madagents.sh`.

## 4. Report

Relay what the installer printed — agents, skills, slates, wiki pages. Read those
numbers rather than passing them on: `example-install.md` says which ones mean the
install worked and which mean it silently did not. Then the two things it cannot do
for them:

- **Start it:** `cd <target> && ./madagents.sh`. A bare `claude` in that folder also
  works but is not the full system: the wrapper is what appends the lead's system
  prompt.
- **MadGraph:** the installed `CLAUDE.md` records that its location is unknown and
  asks the session to fill it in. If the user tells you where MadGraph is, offer to
  write that one line for them. Otherwise leave it — the first session will find out
  and record it. Never guess a path.

If the user has no MadGraph on this machine at all, do not let that go unsaid: the
system installs and runs, but everything it exists to do against a real MadGraph needs
one, and the container path (`./madrun.sh`) brings its own. `troubleshooting.md` has
how to put that without deciding it for them.
