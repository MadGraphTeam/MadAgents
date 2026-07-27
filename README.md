# MadAgents

[![arXiv](https://img.shields.io/badge/arXiv-2601.21015-b31b1b.svg)](https://arxiv.org/abs/2601.21015)

This is the **official implementation** of **MadAgents**.

- 📄 Paper: [arXiv:2601.21015](https://arxiv.org/abs/2601.21015)
- 📦 Supplementary material: [`supplementary/`](supplementary)
- 🗄️ Superseded releases: [`legacy/`](legacy)

---

## Changelog 🔥

- **[26/07/28]** **MadAgents v3** — a new multi-agent system consisting of over 40 specialists, which you can run in a container or install straight into a folder. See [Two ways to run it](#two-ways-to-run-it), [Memory](#memory) and [Skills](#skills) for details. 🔥
- **[26/04/07]** Self-improving docs — MadAgents evaluates itself and refines the MadGraph documentation. *(now in [`legacy/madagents_v2/`](legacy/madagents_v2))*
- **[26/03/20]** Released the first Claude Code implementation — run MadAgents from the terminal with a Claude subscription, no API credits needed. *(now in [`legacy/madagents_v2/`](legacy/madagents_v2))*
- **[26/03/20]** Added Anthropic model support, a physics-expert worker, three specialized reviewers, and parallel worker dispatch to the web version. *(now in [`legacy/madagents_v1/`](legacy/madagents_v1))*

---

## What can I do with MadAgents?

MadAgents is a set of **communicative agents** that support **MadGraph-centered HEP workflows**:

- **Build MadGraph setups** from a physics request — process line, model, parameters, cuts, scales,
  decay chains, EFT orders, LO/NLO
- **Check its own work by running it**, rather than only reasoning about it
- **Ground answers in MG5 source** instead of recall: it caches *where to look*, then reads the
  value fresh, so a version-dependent number is never stale
- **Learn** — findings go into a wiki the next session starts from

---

## Two ways to run it

You can run MadAgents **in a container** or **installed into a folder**. The agent system is
identical either way — the roster, the skills, the memory. What differs is what surrounds it, and
neither one is the real version:

| | `./madrun.sh` | `install/` |
| --- | --- | --- |
| Apptainer | required | not used |
| MadGraph | comes with the image | yours, wherever you have it |
| Runs in | a container, one run per instance | any folder on your machine |
| Deliverables | `<instance>/output/` | the folder itself |
| Isolation | container + a fresh per-run overlay | none — your filesystem, your permissions |
| Fits when | you have no MadGraph, or want runs disposable and isolated | you already have MadGraph, or cannot install Apptainer |

Pick whichever suits the machine you are on; both are first-class, and one clone gives you both.

---

## Quick start

Both paths need a **Linux host** (or a Linux VM on Windows/macOS, see
[Install Apptainer](#install-apptainer)) and the
**[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)**, installed and authenticated
— a Claude subscription or API credits both work. Clone or download this repository, then take
either branch.

### A) In a container — `./madrun.sh`

Also needs **[Apptainer](https://apptainer.org/)** on the host. Brings its own MadGraph, so this is
the path that works on a machine with no HEP stack at all.

```bash
cp config.env.example config.env              # set APPTAINER_DIR and CLAUDE_CONFIG_DIR
./image/create_image.sh --type preinstall     # MadGraph + ROOT + Pythia8 + Delphes
./madrun.sh
```

`madrun.sh` offers a menu — start a new run, resume one, or fork one — then builds that run, starts
the container, and launches Claude Code inside it with the agent system and the memory you chose
already in place. Anything it does not recognise is forwarded to `claude`:

```bash
./madrun.sh --list                                    # your runs
./madrun.sh --new --name ttbar --memory pretrained    # skip the menu
./madrun.sh --fork run_dir/instances/ttbar__<stamp>   # inherit a run's memory
./madrun.sh --resume                                  # forwarded to claude
```

Each run is a self-contained folder under `run_dir/instances/` with its own memory, overlay and
lock — so different runs work concurrently, and the same run cannot be started twice. Deliverables
land in `<instance>/output/`. See [Build image](#build-image) for the other image types.

### B) In a folder — `install/`

No Apptainer, no image, no `config.env`. Uses the MadGraph you already have.

```bash
./install/madinstall.sh                                        # guided: asks where, and which memory
python3 install/installer.py ~/my-study --memory pretrained    # or straight to it

cd ~/my-study && ./madagents.sh
```

An install *is* the folder you work in: the agent system, the memory you picked, and a
`madagents.sh` that starts a session there. The one thing it cannot bring is MadGraph — it records
that the location is unknown and lets the first session find it and write it down. Details:
[`install/README.md`](install/README.md).

> Tip, either way: the shipped system pre-approves nothing, so a plain run asks before each tool
> use. A container run has your home directory mounted; an install has no sandbox at all. Skipping
> those checks (`--dangerously-skip-permissions`) is a real decision — make it explicitly, per run.

---

## Skills

You can invoke any of these by name, and MadAgents reaches for them on its own when a task calls
for one.

| Skill | What it does |
| --- | --- |
| **`/mg-setup`** | Builds the MG5 setup for your request |
| **`/mg-probe`** | Tests a setup by running it |
| **`/mg-deep-verify`** | A thorough re-check, when you want one |
| **`/mg-study`** | Reads up on a topic before you need it |
| **`/ma-wiki-write`** | Saves what it worked out, for next time |
| **`/ma-wiki-lint`** | Tidies its notes |
| **`/ma-reflect`** | Fixes a mistake so it stops recurring |
| **`/ma-doctor`** | Reviews its own setup, with your approval |

---

## Memory

MadAgents remembers in two tiers:

- **Memory** — a short file per specialist, **always loaded**. Its operating principles, its recent
  lessons, and an index of its wiki pages.
- **Wiki** — the long-form pages, **read on demand**. A specialist matches the index in its memory
  file against the task at hand and opens only the pages that apply.

The split is what makes a large body of knowledge affordable: what is always in context stays
short, and the detail is fetched only when it is relevant.

A **memory pack** is what those two tiers hold at the start — of a run, or of an install:

| Pack | Contains | For |
| --- | --- | --- |
| `pretrained` *(default)* | memory + wiki for MG5 | Anthropic models |
| `pretrained-local` | the same, plus harness know-how | a self-hosted model |
| `bare-local` | harness know-how only | a self-hosted model, cold domain |
| `none` | nothing — both tiers empty | the shipped system as-is |

```bash
./madrun.sh --list-memory                 # what each option carries
./madrun.sh --new --memory none           # start completely cold

python3 install/installer.py --list-memory              # the same packs, for an install
python3 install/installer.py ~/my-study --memory none
```

A pack is **copied** in, so a session extends its own copy and the shipped pack stays fixed. Fork a
finished run to carry its accumulated memory into the next one.
Details: [`memory/README.md`](memory/README.md).

The two `-local` packs are for running on a model you host yourself — see
[`local/README.md`](local/README.md).

---

## Configuration

Container runs read `config.env` from the repo root; use `config.env.example` as the template if it
is missing, and note that relative paths resolve from the repo root. An install needs none of this
— it is configured by what the installer writes into the folder.

- `APPTAINER_DIR` — directory containing the `apptainer` binary. The only value most setups need.
- `CLAUDE_CONFIG_DIR` — your Claude Code config dir (e.g. `~/.claude`). Effectively required: it is
  where the session's login and accepted-trust state live.
- `APPTAINER_IMAGE`, `OUTPUT_DIR`, `RUN_DIR` — defaults for a bare run; a run instance sets its own.
- `BIND_SLURM` — bind the host's SLURM config and munge socket so the container's `sbatch`/`squeue`
  reach the same controller. Empty or `auto` binds when the host looks like a submit host.

No API keys here: Claude Code authenticates itself, and `*_API_KEY` / `*_AUTH_TOKEN` variables are
actively stripped from the container environment.

### Temporary overrides (environment variables)

Any value in `config.env` can be overridden for a single run by setting the variable in the caller
environment. Precedence: **caller env > config.env > script defaults**.

```bash
OUTPUT_DIR=/tmp/madagents_out ./madrun.sh
```

---

## Build image

```bash
./image/create_image.sh --type preinstall   # MG5_aMC + ROOT + Pythia8 + Delphes + FastJet + LHAPDF6
./image/create_image.sh --type minimal      # MG5_aMC + ROOT only — faster build, smaller image
./image/create_image.sh --type clean        # no preinstalled tools
./image/create_overlay.sh                   # rebuild just the base overlay
```

Each image type owns a folder — `image/preinstall/`, `image/minimal/`, `image/clean/` — holding its
definition, the `.sif` built from it, and a `CLAUDE.md` describing what that build installs and
where. `--type preinstall` therefore produces `image/preinstall/madagents.sif`, and the launcher
runs whichever type is built (`APPTAINER_IMAGE` overrides). A base overlay
`image/mad_overlay.img` (~10 GB, sparse) is written alongside; each run instance then gets a fresh
sparse overlay of its own, which is what lets instances run concurrently.

The `CLAUDE.md` beside an image is the environment description every run built on it starts from —
see [Data, outputs, and persistence](#data-outputs-and-persistence).

The preinstall build downloads two tarballs; if the upstream links move, update them in
`image/preinstall/image.def`.

---

## Install Apptainer

Only the container path needs Apptainer — if you already have MadGraph, [install into a
folder](#b-in-a-folder--install) instead and skip this. The Windows/macOS note below applies to
both paths, though: MadAgents runs on Linux either way.

We use Apptainer because it can *often* be installed and run **without sudo** (rootless), which
matters on HPC clusters where users have no admin rights.

- [Installation guide](https://apptainer.org/docs/admin/main/installation.html)
- [Unprivileged install from pre-built binaries](https://apptainer.org/docs/admin/main/installation.html#install-unprivileged-from-pre-built-binaries)
- [Windows / macOS](https://apptainer.org/docs/admin/main/installation.html#installation-on-windows-or-mac) — needs a Linux VM (WSL2 on Windows, Lima on macOS)

If installation is not possible in your environment, ask your cluster administrator for a site-wide
Apptainer install.

---

## Stop / cleanup

Only container runs need this — an install has no instance to stop; closing the session is all.

A run stops its own Apptainer instance on exit. `cleanup_madrun.sh` is for a wedged run or a dead
terminal:

```bash
./cleanup_madrun.sh
```

Manual fallback: `apptainer instance list`, then `apptainer instance stop INSTANCE_NAME`.

---

## Data, outputs, and persistence

An install keeps all of this in the installed folder itself, which is the session's project root:
deliverables beside `.madagents/wiki/`, and its own `CLAUDE.md`. For a container run:

- `<instance>/output/` is the session's project root — deliverables and the wiki land there.
- `<instance>/output/CLAUDE.md` describes the filesystem the session works in: where it starts,
  where scratch is, and what the image installed. It is seeded once when the run is created, copied
  from the `CLAUDE.md` beside the image being used, and belongs to the session from then on — the
  overlay is writable, so what is installed drifts from what the image shipped, and the session is
  asked to keep the description current. Nothing overwrites its edits.
- `<instance>/run/` holds logs and the run lock, and can be deleted when you are done.
- Each instance carries **its own** overlay (`<instance>/overlay.img`), so changes inside the
  container persist across restarts of that run — and two runs never fight over one overlay.

Want a "clean slate" run? Start a fresh instance rather than deleting anything:

```bash
./madrun.sh --new --memory none
```

That gives you a new overlay, an empty learned tier and an empty `output/`, leaving every existing
run untouched.

---

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| An install cannot find MadGraph | Nothing points it there yet. Write the path into the folder's `CLAUDE.md`, or let the session find it and record it. |
| An install came up with no memory | Either the folder is not its own git root — Claude Code then resolves the project root to the enclosing repository and reads the slates from there; fix with `git init` in the folder — or it was moved and `madagents.sh` could not re-point auto-memory because `python3` is not on `PATH`. |
| An install behaves like plain Claude Code | Started with a bare `claude`. Use `./madagents.sh`: it is what appends the lead's system prompt. |
| `config.env not found` | Run from the repo root, or copy `config.env.example` to `config.env`. |
| `apptainer not found` | Install Apptainer, or set `APPTAINER_DIR` in `config.env`. |
| Build fails | The build uses `apptainer build --fakeroot`. If your site disallows fakeroot, build elsewhere and share the `.sif` via `APPTAINER_IMAGE`, or ask admins about enabling user namespaces. |
| Preinstall build fails | Tarball URLs in `image/preinstall/image.def` may have moved — update and retry. |
| The run says it cannot take the lock | That instance is already running. Use another instance, or `./cleanup_madrun.sh`. |
| None of the memory loaded | `autoMemoryEnabled` is pinned per instance; check it was not overridden in your own Claude config. See [`memory/README.md`](memory/README.md). |

---

## Legacy releases

Earlier MadAgents releases are kept in [`legacy/`](legacy). See
[`legacy/README.md`](legacy/README.md).

---

## Citation

If you used MadAgents in your research, please cite us as follows:

```bibtex
@article{Plehn:2026gxv,
    author = "Plehn, Tilman and Schiller, Daniel and Schmal, Nikita",
    title = "{MadAgents}",
    eprint = "2601.21015",
    archivePrefix = "arXiv",
    primaryClass = "hep-ph",
    month = "1",
    year = "2026"
}
```
