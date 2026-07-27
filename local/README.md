# Running MadAgents on a self-hosted model

MadAgents normally runs on Claude Code's own authentication — a Claude
subscription or API credits. This folder is the other case: pointing a session
at **your own endpoint** that speaks the Anthropic `/v1/messages` API, so the
agent system runs on a model you host.

```bash
cp local/config.env.example local/config.env    # set LOCAL_MODEL_BASE_URL
./local/madrun.sh
```

Everything else is shared with the normal run: the same container image, the
same overlay, the same run instances under `run_dir/instances/`, the same
memory packs. Only the model behind the session changes.

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
| `LOCAL_MODEL_BASE_URL` | **Required.** Your endpoint, e.g. `http://my-gpu-node:8000`. Without it the launcher refuses to start rather than quietly falling back to Anthropic. |
| `LOCAL_MODEL_TOKEN` | Bearer token, if your endpoint authenticates. Leave empty if not. |
| `LOCAL_MODEL_NAME` | Model to request, passed as `--model`. |
| `LOCAL_MODEL_EFFORT` | `low` … `max`, passed as `--effort`. Leave empty unless your endpoint implements it. |

Precedence is **caller env > `local/config.env` > defaults**, so any value can
be overridden for one run:

```bash
LOCAL_MODEL_NAME=my-other-model ./local/madrun.sh
```

Do **not** set `ANTHROPIC_BASE_URL` or `ANTHROPIC_AUTH_TOKEN` yourself, in this
file or in your shell. Those names are scrubbed unconditionally, so they would
do nothing for a normal run and be confusing here. The rename happens inside
this launcher, at the moment the session starts.

---

## Which memory pack to use

A smaller open-weights model benefits from being told how the Claude Code
harness works — chiefly how to wait for a dispatched subagent, which a frontier
model gets right unprompted. Two of the shipped packs carry exactly that:

```bash
./madrun.sh --list-memory
```

- **`pretrained-local`** — the MadGraph knowledge plus that harness know-how.
- **`bare-local`** — the harness know-how alone, for measuring what the MadGraph
  knowledge is worth on your model.

A pack chooses what the agent *knows*; it never chooses which model it runs on.
That is what this folder is for. See [`../memory/README.md`](../memory/README.md).

---

## Notes

- **Your endpoint must speak the Anthropic `/v1/messages` API**, including tool
  use. An OpenAI-compatible server needs a translating proxy in front of it.
- **Serving the model is out of scope here.** This folder connects to an
  endpoint; it does not start one.
- **Sessions are long and tool-heavy.** The agent system dispatches many
  subagents, so a self-hosted run is far more sensitive to throughput and
  context limits than a single chat would be.
