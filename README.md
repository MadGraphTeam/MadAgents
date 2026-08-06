# MadAgents

[![arXiv](https://img.shields.io/badge/arXiv-2601.21015-b31b1b.svg)](https://arxiv.org/abs/2601.21015)
[![arXiv](https://img.shields.io/badge/arXiv-2607.22813-b31b1b.svg)](https://arxiv.org/abs/2607.22813)

This is the **official implementation** of **MadAgents**.

- 📄 Paper: [arXiv:2601.21015](https://arxiv.org/abs/2601.21015), [arXiv:2607.22813](https://arxiv.org/abs/2607.22813)
- 📦 Supplementary material: [`supplementary/`](supplementary)
- 🗄️ Superseded releases: [`legacy/`](legacy)

---

## Changelog 🔥

- **[26/08/04]** **Extended harness support** — Codex, opencode, and self-hosted models. See [Which CLI](#which-cli).
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

The container path has one variant: [`./local/madrun.sh`](#c-on-a-model-you-host--localmadrunsh)
builds the same runs against **a model you host yourself** instead of a vendor API.

---

## Which CLI

MadAgents runs on **Claude Code** (default), on **Codex**, or on **opencode**. The agent system is
the same on all three — the same 46 specialists, the same 8 skills, the same memory packs — because
the Codex and opencode trees are *generated* from the Claude Code one and checked in beside it.

```bash
./madrun.sh --new --provider codex   # a container run on Codex
cd install && codex                  # a folder install, done by a Codex session
./local/madrun.sh                    # opencode, against a model you host
```

Each needs its CLI installed and authenticated:
**[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (a Claude subscription or API
credits), the **[Codex CLI](https://developers.openai.com/codex)** (a ChatGPT plan or API credits),
or **[opencode](https://opencode.ai)** (a single binary, which this repository does not vendor).
None of them reads a key from your shell — see [Configuration](#configuration).

The installer runs on either of the two hosted CLIs, and the two choices are independent —
`cd install && claude` can build a Codex install, and `cd install && codex` can build a
Claude Code one.

Which CLI is available where is **not** symmetric:

| | Claude Code | Codex | opencode |
| --- | --- | --- | --- |
| `./madrun.sh` — a vendor API | ✔ default | ✔ | ✘ |
| `./local/madrun.sh` — your own endpoint | ✔ | ✘ | ✔ default |
| `install/` — a folder | ✔ default | ✔ | ✘ |

opencode leads on the self-hosted path because it is the only one of the three that reaches an
endpoint through a **config file** rather than an environment variable. Codex is absent there for
the mirror-image reason — it has no endpoint redirection this launcher supports. See
[`local/README.md`](local/README.md).

What differs is only how each CLI is told about the system:

| | Claude Code | Codex | opencode |
| --- | --- | --- | --- |
| Roster | `.claude/agents/*.md` | `.codex/agents/*.toml` | `.opencode/opencode.json` + `.opencode/cards/` |
| Skills | `.claude/skills/` | `.agents/skills/` | `.claude/skills/`, read natively |
| Environment description | `CLAUDE.md` | `AGENTS.md` | `AGENTS.md` |
| A consultant's always-loaded slate | `agent-memory/<name>/MEMORY.md` | a marked region inside its own role file | `agent-memory/<name>/MEMORY.md`, pulled in by `{file:}` |

The Codex column is the one worth knowing about: there a consultant's memory travels *inside* the
file that defines it, because that file is what Codex loads on every dispatch of that role. It is
written by a bundled script rather than by hand, since a malformed edit would drop the consultant
from the roster with no error. opencode needs no such splice — it interpolates the slate file into
the prompt when config loads. Nothing else about using the system changes.

> A run instance and an install are **per-provider**. You can have both side by side, but there is
> no conversion between them — a Codex run cannot inherit a Claude Code run's memory, and a fork
> keeps the provider it was forked from.

Changing the agent system means editing `madagents/` and re-rendering **both** generated trees:

```bash
python3 tools/render_codex.py               # regenerate madagents_codex/
python3 tools/render_opencode.py            # regenerate madagents_opencode/
python3 tools/render_codex.py --check       # fail if a tracked tree is stale
python3 tools/render_opencode.py --check
```

---

## Quick start

Both paths need a **Linux host** (or a Linux VM on Windows/macOS, see
[Install Apptainer](#install-apptainer)) and one of the two CLIs above, installed and
authenticated. Clone or download this repository, then take either branch.

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
./madrun.sh --new --provider codex                    # run it on Codex instead
./madrun.sh --fork run_dir/instances/ttbar__<stamp>   # inherit a run's memory
./madrun.sh --resume                                  # forwarded to claude
```

Each run is a self-contained folder under `run_dir/instances/` with its own memory, overlay and
lock — so different runs work concurrently, and the same run cannot be started twice. Deliverables
land in `<instance>/output/`. See [Build image](#build-image) for the other image types.

### B) In a folder — `install/`

No Apptainer, no image, no `config.env`. Uses the MadGraph you already have.

```bash
cd install && claude                            # or: cd install && codex
                                                # it asks where, which memory, and which CLI to install for
cd ~/my-study && ./madagents.sh                 # start a session on the install

python3 install/installer.py verify ~/my-study  # check an install is intact (read-only)
```

The session performs the install itself — there is no installer script beyond the
read-only `verify`. It surveys the folder first and never removes a path it did not
install, so **installing into a repository you already work in is supported**, not a
hazard.

An install *is* the folder you work in: the agent system, the memory you picked, and a
`madagents.sh` that starts a session there. The one thing it cannot bring is MadGraph — it records
that the location is unknown and lets the first session find it and write it down. Details:
[`install/README.md`](install/README.md).

> Tip, whichever path: the shipped system pre-approves nothing — on **all three** providers, it ships no
> permissions block and no launcher flags, so a plain run asks before each tool use. A container run
> has your home directory mounted; an install has no sandbox at all. Skipping those checks
> (`--dangerously-skip-permissions`, or `--dangerously-bypass-approvals-and-sandbox` on Codex) is a
> real decision — make it explicitly, per run.
>
> On Codex that includes the agents' own memory: a consultant's slate lives in
> `.codex/agents/<name>.toml`, which Codex's default sandbox keeps read-only, so `/ma-wiki-write`
> asks. Interactively that is one prompt. Unattended (`codex exec`) it fails instead of asking,
> which is the case for the bypass flag above.

### C) On a model you host — `./local/madrun.sh`

Same container, same overlay, same run instances, same memory packs; only the model behind the
session changes. The default CLI here is **opencode**.

```bash
cp local/config.env.example local/config.env   # LOCAL_PROVIDER + LOCAL_MODEL_BASE_URL
./local/madrun.sh
```

Runs built by either launcher live in `run_dir/instances/`, so `--list` shows all of them, with a
`BACKEND` column saying which start path each was built for; a run's backend is fixed when it is
built. Pick the memory pack whose suffix matches the CLI — see [Memory](#memory). Details:
[`local/README.md`](local/README.md).

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
| `pretrained-local-cc` / `-opencode` | the same, plus harness know-how for that CLI | a self-hosted model |
| `bare-local-cc` / `-opencode` | that harness know-how only | a self-hosted model, cold domain |
| `none` | nothing — both tiers empty | the shipped system as-is |

```bash
./madrun.sh --list-memory                 # what each option carries
./madrun.sh --new --memory none           # start completely cold
./local/madrun.sh --new --memory pretrained-local-opencode   # a self-hosted run
```

An install offers the same packs — the installer session lists them and asks, so there
is nothing to pass. An install is a Claude Code or a Codex one, so the `-opencode` packs
never apply to it.

**Match the suffix to the CLI.** `-cc` states Claude Code's mechanic for how a dispatched
subagent's work comes back; opencode's is different, and a lead given the wrong one ends
its turn waiting to be re-invoked and simply stops. Nothing detects that for you.

A pack is **copied** in, so a session extends its own copy and the shipped pack stays fixed. Fork a
finished run to carry its accumulated memory into the next one.
Details: [`memory/README.md`](memory/README.md).

The four `-local` packs are for running on a model you host yourself — see
[`local/README.md`](local/README.md).

---

## Configuration

Container runs read `config.env` from the repo root; use `config.env.example` as the template if it
is missing, and note that relative paths resolve from the repo root. An install needs none of this
— it is configured by what the installer writes into the folder.

- `APPTAINER_DIR` — directory containing the `apptainer` binary. The only value most setups need.
- `CLAUDE_CONFIG_DIR` — your Claude Code config dir (e.g. `~/.claude`). Effectively required: it is
  where the session's login and accepted-trust state live.
- `CODEX_HOME` — the same thing for a `--provider codex` run (e.g. `~/.codex`), and required for the
  same reason. The launcher also marks the container's mount roots trusted there: untrusted, Codex
  ignores the project's `.codex/` layer entirely and the consultants silently do not load.
- `OPENCODE_DIR` — directory containing the `opencode` binary, for a self-hosted run. This
  repository does not vendor it, and it usually lives off `PATH`. Left empty, the launcher looks on
  `PATH`, then in the usual install prefixes, and finally installs opencode inside the container.
- `OPENCODE_HOME` — one directory holding opencode's four XDG roots, bind-mounted so runs share
  them. Worth setting: opencode fetches a ~3.4 MB model catalogue at startup, so a populated cache
  is what lets a session start at all on a node with no network egress.
- `OPENCODE_ENABLE_WEBSEARCH` — opt in to opencode's `websearch` tool, hidden from a self-hosted
  provider by default. Read the note in `config.env.example` before enabling it: two consultants are
  told to verify PDG constants and citations by search, and both fall back silently to recall
  without it.
- `APPTAINER_IMAGE`, `OUTPUT_DIR`, `RUN_DIR` — defaults for a bare run; a run instance sets its own.
- `BIND_SLURM` — bind the host's SLURM config and munge socket so the container's `sbatch`/`squeue`
  reach the same controller. Empty or `auto` binds when the host looks like a submit host.

No API keys here: the CLI authenticates itself, and `*_API_KEY` / `*_AUTH_TOKEN` variables — plus
the endpoint-redirection ones for every provider — are actively stripped from the container
environment. A self-hosted endpoint is the one exception, and it is declared in `local/config.env`
rather than here: see [`local/README.md`](local/README.md).

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
- `<instance>/output/CLAUDE.md` (or `AGENTS.md` on Codex and opencode) describes the filesystem the session works
  in: where it starts, where scratch is, and what the image installed. It is seeded once when the run
  is created, copied from the `CLAUDE.md` beside the image being used, and belongs to the session
  from then on — the
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
| A Codex session has no consultants | The project is not trusted, so Codex ignored `.codex/` — it asks once on the first run in a folder; answer yes. Trust has to be *recorded* in `$CODEX_HOME/config.toml`; a `-c projects…trust_level` override does **not** load the project layer. Verify by asking whether `spawn_agent` has an `agent_type` parameter — no parameter means no roles loaded. |
| Every command dies with `bwrap: Can't bind mount /oldroot/ on /newroot/` | Codex's sandbox is bubblewrap, which cannot nest inside Apptainer's user namespace, so its default `workspace-write` mode cannot work in a container run. The launcher does not choose a sandbox for you — start the session with `./run.sh --sandbox danger-full-access` (argv is forwarded to `codex`). The container is then the boundary: a per-instance overlay under `--cleanenv`, seeing only the bound paths — the same boundary the Claude Code side relies on. An install (no container) is unaffected and keeps Codex's sandbox. |
| A Codex consultant asks approval for `/ma-wiki-write` | Expected on the **first** one: its slate lives in `.codex/agents/<name>.toml`, which Codex's default sandbox keeps read-only. Choose "add to allow list" and Codex records it in `$CODEX_HOME/rules/default.rules`; every later run skips the prompt. If it keeps asking, the run has no `CODEX_HOME` bound — set it in `config.env`. |
| Under `codex exec`, a slate write fails instead of asking | Non-interactive runs cannot surface a fresh approval, so the action fails. Approve it once interactively, or use `--dangerously-bypass-approvals-and-sandbox`. |
| A Codex skill never fires | Its `description:` is invalid YAML (usually an unquoted `": "`), so Codex drops it silently. `python3 tools/render_codex.py` normalises this — re-render rather than hand-editing `madagents_codex/`. |
| `madagents_codex/` is out of date | Re-render it: `python3 tools/render_codex.py`. `--check` reports staleness without writing. |
| A render fails on a changed override | A file under `tools/codex_overrides/` or `tools/opencode_overrides/` was written against an older version of its source. Fold the change in, then `python3 tools/refresh_override_hashes.py` (add `--manifest tools/opencode_overrides/OVERRIDES.toml` for the opencode side). |
| An opencode run reports success but nothing was written | `opencode run` never prompts — it **auto-rejects** anything set to `ask`, and the shipped block sets `edit: ask`, so every slate write fails while the agent narrates success. Interactively there is no problem; scripted runs want `./run.sh run --auto …`. |
| An opencode session refuses to start, or has no consultants | opencode hard-fails on invalid config, and a `{file:}` target that does not exist takes the whole 46-agent roster down with it. Re-render rather than hand-editing: `python3 tools/render_opencode.py`. |
| `madagents_opencode/` is out of date | Re-render it: `python3 tools/render_opencode.py`. `--check` reports staleness without writing. |
| An opencode consultant cannot search the web | `websearch` is hidden from a self-hosted provider unless `OPENCODE_ENABLE_WEBSEARCH=1` is set in `config.env`. |
| `./madrun.sh --provider opencode` is refused | opencode is only offered on the self-hosted path. Use `./local/madrun.sh`. |
| `config.env not found` | From `image/create_image.sh` or `image/create_overlay.sh`, the two scripts that require it. Run from the repo root, or copy `config.env.example` to `config.env`. |
| `apptainer not found` | Install Apptainer, or set `APPTAINER_DIR` in `config.env`. A *missing* `config.env` is tolerated silently by `./madrun.sh`, so a fresh clone reports this rather than complaining about the config. |
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

```bibtex
@article{Diefenbacher:2026azr,
    author = "Diefenbacher, Sascha and Plehn, Tilman and Schiller, Daniel and Schmal, Nikita",
    title = "{Agentic Re-Casting using Agentic Re-Simulations}",
    eprint = "2607.22813",
    archivePrefix = "arXiv",
    primaryClass = "hep-ph",
    month = "7",
    year = "2026"
}
```
