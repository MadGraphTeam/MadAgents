# Running MadAgents on a self-hosted model

MadAgents normally runs on the vendor CLI's own authentication — a Claude or
ChatGPT subscription, or API credits. This folder is the other case: pointing a
session at **your own endpoint**, so the agent system runs on a model you host.

Which API that endpoint has to speak depends on the CLI you run it through, and
that is the one decision to make first:

- **opencode** *(default)* — any **OpenAI-compatible** endpoint (`/v1/chat/completions`).
- **claude_code** — an endpoint speaking the **Anthropic `/v1/messages`** API, tool use included.

```bash
cp local/config.env.example local/config.env    # set LOCAL_PROVIDER + LOCAL_MODEL_BASE_URL
./local/madrun.sh
```

Everything else is shared with the normal run: the same container image, the
same overlay, the same run instances under `run_dir/instances/`, the same
memory packs. Only the model behind the session changes.

---

## The menu

`./local/madrun.sh` shows the same menu as the repo-root `./madrun.sh`, because it
*is* the same menu — one implementation, told to build new runs for the local
backend. It lists your runs, resumes one, starts a new one, or forks an old one's
memory, then launches it:

```bash
./local/madrun.sh --list                                   # your runs
./local/madrun.sh --new --memory pretrained-local-opencode --name qwen-study
./local/madrun.sh --fork run_dir/instances/qwen-study__<stamp>
./local/madrun.sh --resume                                 # forwarded to the CLI
```

Runs live in one place, `run_dir/instances/`, whichever launcher built them, so
`--list` shows all of them rather than half. A **`BACKEND`** column says which
start path each was built for:

```
     NAME                   CLI          BACKEND  MEMORY            WIKI              LAST USED
  1) qwen-study             opencode     local    pretrained-local-o…  7 wiki pages   2h ago
  2) madagents             claude_code  hosted   pretrained          31 wiki pages   1d ago
```

A run's backend is **fixed when it is built**, and its generated `run.sh` is the
authority: a `local` instance always comes up against your endpoint, and a
`hosted` one always comes up against the vendor API — no matter which launcher
you started it from. A fork inherits its source's backend.

The endpoint is checked before the menu, not after: with no
`LOCAL_MODEL_BASE_URL` the launcher says so immediately rather than asking you
questions it cannot act on. `--list` is exempt, since listing needs no model.
The banner shows which endpoint a new run will talk to, with the token redacted.

> **Not every CLI can run locally.** The menu only offers providers this path
> supports (`opencode`, `claude_code`), and building or starting an unsupported
> one — a Codex instance, say — fails with a sentence saying so rather than an
> apptainer bind error.

---

## Which CLI: opencode or Claude Code

Both reach your endpoint; they differ in *how*, and that difference is the reason
opencode is the default here.

| | opencode *(default)* | claude_code |
| --- | --- | --- |
| Endpoint speaks | OpenAI-compatible `/v1/chat/completions` | Anthropic `/v1/messages`, incl. tool use |
| Endpoint declared in | a config **file** the launcher generates per run | `ANTHROPIC_BASE_URL` in the container env |
| API key | a `{file:}` reference to a `0600` file | `ANTHROPIC_AUTH_TOKEN` in the container env |
| Key ever in the environment | **no** | yes, unavoidably |

That last row is not cosmetic. The root `./madrun.sh` strips every credential and
endpoint variable and *asserts* they are gone before starting a session; the
claude_code local path has to skip that assertion, because the only way to point
Claude Code elsewhere is the variable it scrubs. opencode needs no such hole, so
the opencode path runs the assertion — it is the only local path where that
guarantee still holds end to end.

Set which one you want with `LOCAL_PROVIDER` in `local/config.env`, or per run
with `--provider`. An existing run keeps whatever it was built with.

> **Unattended opencode runs need `--auto`.** The shipped system pre-approves
> nothing, so `edit` is set to `ask`. `opencode run` never prompts — it
> **auto-rejects** anything set to `ask`, so every slate write fails and
> `/ma-wiki-write` reports success while changing nothing. Interactively the
> prompt appears and all is well; scripted or benchmark runs want
> `./run.sh run --auto …`, which is opencode's counterpart to
> `--dangerously-skip-permissions`. Codex behaves the same way under
> `codex exec`.

**opencode needs the `opencode` CLI**, which this repository does not ship — a
single binary from the upstream release. Set **`OPENCODE_DIR`** in the repo-root
`config.env` to the directory holding it, exactly as `APPTAINER_DIR` names
apptainer's; leave it empty and the launcher looks on `PATH`, then in the usual
install prefixes, and finally installs opencode inside the container. Set it
wrong and you get a message saying so, rather than a silent fallback.

Set **`OPENCODE_HOME`** there too: opencode downloads a ~3.4 MB model catalogue
at startup, and pointing its four XDG roots at one directory lets runs share it —
which is what a compute node without network egress needs.

**Web search is opt-in.** opencode hides its `websearch` tool from a self-hosted
provider; a session gets `webfetch` (fetch a known URL) but no way to *find*
one. `OPENCODE_ENABLE_WEBSEARCH=1` in `config.env` turns it on — no API key, and
verified working from inside the container. It is off by default because the
keyless path sends every query to Exa's hosted service, a third party you have no
contract with, under an undocumented rate limit. That matters concretely:
`ma-physics-consultant` and `ma-numerics-consultant` are told to verify PDG
constants and literature citations by web search, and without the tool they fall
back to pretrained recall — which is what those cards exist to prevent. Read the
note in `config.env.example` before deciding.

On opencode the agent system is the same 46 consultants and 8 skills, rendered by
`python3 tools/render_opencode.py`. A consultant's learned tier stays a plain
`.claude/agent-memory/<name>/MEMORY.md` — the same file Claude Code auto-loads —
pulled into its prompt by `{file:}` interpolation. So the memory packs seed a
Codex-free, translation-free copy, and `/ma-wiki-write` writes an ordinary
markdown file.

---

## Why this is a separate launcher

The root `./madrun.sh` **strips every API key and endpoint-redirection
variable** from the container environment, and asserts they are gone
immediately before it starts the session. That is a guarantee worth keeping
absolute: nothing you happen to have exported in your shell can reach a
MadAgents run, and reading the code should make that obvious in one place.

Running on your own endpoint needs the exact opposite — `ANTHROPIC_BASE_URL`
has to reach the session. Rather than add an exception to that guarantee, this
case lives here, as its own launcher with its own config file:

| | Root `./madrun.sh` | `./local/madrun.sh` |
| --- | --- | --- |
| Model | Anthropic, via Claude Code's login | your endpoint |
| Config | `config.env` | `config.env` **and** `local/config.env` |
| Ambient `ANTHROPIC_*` from your shell | stripped | stripped |
| Endpoint reaching the session | never | only what `local/config.env` declares |

The two share the container machinery by importing it; they share nothing about
authentication. `src/launcher/` has no knowledge that this folder exists.

---

## Configuration

All of it lives in `local/config.env` (git-ignored — the token is a real
credential). See [`config.env.example`](config.env.example) for the full
commentary.

| Variable | |
| --- | --- |
| `LOCAL_PROVIDER` | Which CLI a **new** run is built for: `opencode` (default) or `claude_code`. This is what decides which API the endpoint below must speak. An existing run keeps whatever it was built with. |
| `LOCAL_MODEL_BASE_URL` | **Required.** Your endpoint. Include the `/v1` suffix for `opencode` (`http://my-gpu-node:8000/v1`), omit it for `claude_code` (`http://my-gpu-node:8000`). Without it the launcher refuses to start rather than quietly falling back to a hosted API. |
| `LOCAL_MODEL_TOKEN` | Bearer token, if your endpoint authenticates. Leave empty if not. On `opencode` it is written to a `0600` file the generated config references; on `claude_code` it becomes `ANTHROPIC_AUTH_TOKEN` in the container. |
| `LOCAL_MODEL_NAME` | Model to request. On `opencode`, the id your server returns from `GET /v1/models`; it becomes the session default, addressed as `local/<name>`. Strongly recommended there — without it the provider declares no models and you pick one in the TUI. On `claude_code`, passed as `--model`. |
| `LOCAL_MODEL_EFFORT` | `low` … `max`, passed as `--effort`. **`claude_code` only** — the opencode path passes no model flags at all. Leave empty unless your endpoint implements it. |

Where the `opencode` binary lives, and where its config/cache/session roots
live, are *not* set here — `OPENCODE_DIR` and `OPENCODE_HOME` belong beside
`APPTAINER_DIR` in the repo-root `config.env`, which this launcher also reads.
This file is only about the endpoint.

Precedence is **caller env > `local/config.env` > defaults**, so any value can
be overridden for one run:

```bash
LOCAL_MODEL_NAME=my-other-model ./local/madrun.sh
```

Do **not** set `ANTHROPIC_BASE_URL` or `ANTHROPIC_AUTH_TOKEN` yourself, in this
file or in your shell. Those names are scrubbed unconditionally, so they would
do nothing for a normal run and be confusing here. On the `claude_code` path the
rename happens inside this launcher, at the moment the session starts; on the
`opencode` path nothing credential-shaped enters the environment at all.

---

## Which memory pack to use

A smaller open-weights model benefits from being told how *its* harness returns a
dispatched subagent's work — something a frontier model gets right unprompted.
That mechanic differs per CLI, so the packs that carry it come in matched pairs:

```bash
./local/madrun.sh --list-memory
```

- **`pretrained-local-opencode`** / **`bare-local-opencode`** — for a `--provider opencode` run.
- **`pretrained-local-cc`** / **`bare-local-cc`** — for a `--provider claude_code` run.

In each pair, `pretrained-*` is the MadGraph knowledge plus that know-how, and
`bare-*` is the know-how alone — the honest cold arm for measuring what the
MadGraph knowledge is worth on your model.

> **Match the pack to the CLI.** The `-cc` packs state Claude Code's mechanic:
> end the turn with no tool call, and the harness re-invokes you with the result.
> opencode has no such mechanic — it returns a consultant's full reply as the
> `task` call's own result — so a lead given the `-cc` bullet on opencode would
> end its turn waiting to be re-invoked and simply stop, losing the dispatched
> work. Seeding either pack onto the wrong provider is a silent behavioural bug,
> not a mismatch the launcher can detect for you.

A pack chooses what the agent *knows*; it never chooses which model it runs on.
That is what this folder is for. See [`../memory/README.md`](../memory/README.md).

---

## Notes

- **Your endpoint must speak the API its CLI expects** — OpenAI-compatible
  `/v1/chat/completions` for `opencode`, Anthropic `/v1/messages` including tool
  use for `claude_code`. Neither path translates between the two: match
  `LOCAL_PROVIDER` to what you actually serve, or put a translating proxy in
  front of it.
- **Serving the model is out of scope here.** This folder connects to an
  endpoint; it does not start one.
- **Sessions are long and tool-heavy.** The agent system dispatches many
  subagents, so a self-hosted run is far more sensitive to throughput and
  context limits than a single chat would be.
- **What opencode actually does**, established by running it rather than by
  reading about it — directory layout, `{file:}` interpolation, the permission
  defaults, the offline behaviour — is written down in
  [`OPENCODE_NOTES.md`](OPENCODE_NOTES.md).
