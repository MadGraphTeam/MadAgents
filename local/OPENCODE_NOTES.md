# opencode mechanics — verified, not recalled

What the opencode runtime actually does, established by running it rather than by reading about it.
The docs were wrong or silent on several of these. Re-verify before trusting any line here against a
different version.

**Verified against:** opencode `1.18.11`, Linux x86-64, glibc 2.41 host.
Installed to a prefix **outside this repository** — never vendored, the same way `claude` and
`codex` are obtained. Point `OPENCODE_BIN` at it, or put it on `PATH`.

> opencode ships a built-in skill, `customize-opencode`, whose body is the authoritative config
> reference — every path, key and shape below is cross-checked against it. Read it with
> `opencode debug skill`. It states the schema at <https://opencode.ai/config.json> is the source of
> truth, and that opencode **hard-fails on invalid config**.

## The introspection surface

This is the reason most of this file could be established offline. `opencode debug` resolves config
the same way a session does:

| Command | Answers |
|---|---|
| `opencode debug paths` | data / config / cache / state / bin / log directories |
| `opencode debug config` | the fully merged, fully interpolated config |
| `opencode debug agent <name>` | one agent's resolved prompt and permissions |
| `opencode debug skill` | every discovered skill, with its resolved path and content |
| `opencode agent list` | the live roster |

`opencode debug agent <name>` is worth singling out: it prints the **resolved prompt**, so
"did the learned tier actually load?" is a question with an offline answer.

## Directories — four XDG variables, not one

There is no `OPENCODE_HOME`. `HOME` alone is **not** enough: it moves `config` and `state` only.
All four XDG variables are honoured, and all four must be set to relocate a session:

```
XDG_CONFIG_HOME  → <dir>/opencode/            opencode.json, agent(s)/, command(s)/, skill(s)/, plugin(s)/
XDG_DATA_HOME    → <dir>/opencode/            auth.json, log/, repos/, project/ (sessions)
XDG_CACHE_HOME   → <dir>/opencode/            models.json, bin/
XDG_STATE_HOME   → <dir>/opencode/
```

Under `--cleanenv` the launcher must set all four explicitly.

## Agents

- **Both directory spellings work.** `.opencode/agent/<name>.md` and `.opencode/agents/<name>.md`
  are both loaded — verified by planting one probe in each and seeing both in `agent list`. Same for
  `command(s)/` and `skill(s)/`. The docs' disagreement with the migration guides is a non-issue.
- The markdown **body becomes the prompt**. Do not also set `prompt:` in frontmatter.
- Allowed frontmatter: `name, model, variant, description, mode, hidden, color, steps, options,
  permission, disable, temperature, top_p`. **Any unknown field is silently routed into `options`** —
  a silent-failure class of the same family as Codex's dropped-on-invalid-YAML skills. A typo'd key
  does not error; it just stops doing anything.
- `mode` is `primary` | `subagent` | `all`. Built-ins: `build`, `plan`, `general`, `explore`
  (+ hidden `compaction`, `title`, `summary`).

## `{file:}` interpolation — the load-bearing finding

`{file:path}` and `{env:VAR}` substitute into config **string values**, and **several may be composed
in one string**. Shell-style `${VAR}` is not substituted.

Verified with an agent declared in `opencode.json` as:

```json
"prompt": "{file:./cards/ma-test-consultant.md}\n\n{file:./.claude/agent-memory/ma-test-consultant/MEMORY.md}"
```

`opencode debug agent ma-test-consultant` resolved `prompt` to exactly the card body, a blank line,
then the slate. **This is what lets the learned tier stay a separate `MEMORY.md` at the Claude Code
path** — no marked region, no splice, no re-parse guard, no `write_slate.py`. It is the one place
where mirroring Claude Code is not merely a preference but is *simpler* than the Codex approach.

Two consequences worth stating:

- Interpolation happens **when config is loaded**, and config is loaded once at startup and never
  hot-reloaded. So a slate the agent rewrites is live from the *next* session — the same semantics as
  Claude Code's auto-memory, for the same reason.
- It works in `provider.<id>.options.apiKey` too, from an absolute path. Verified end-to-end: a
  `0600` file containing a token reached the endpoint as `Authorization: Bearer <token>`. That is
  what keeps the credential out of the config file, out of the environment, and out of anything a
  fork would copy.

## Two relative bases in one file, and one fatal reference

Three facts that look like details and are not:

1. **`{file:}` resolves against the config file's directory.** With the config at
   `.opencode/opencode.json`, a card is `{file:./cards/x.md}` and a slate is
   `{file:../.claude/agent-memory/x/MEMORY.md}`. Absolute paths also work, which is what the
   generated endpoint overlay uses for its token.
2. **`instructions` resolves against the PROJECT ROOT**, not the config's directory. Spelling it
   `../prompts/lead-discipline.md` from `.opencode/` loads **nothing**, silently — verified by
   grepping the request body reaching the model. It must be `prompts/lead-discipline.md`.
3. **A `{file:}` target that does not exist is fatal.** opencode rejects the whole config —
   *"Configuration is invalid … bad file reference … does not exist"* — so a single missing slate
   takes the entire 46-agent roster down. `instructions` is the opposite: a missing file there is
   skipped without a word.

(3) is why the rendered tree ships a cold slate skeleton for every agent that references one, and
why `setup._backfill_opencode_slates` re-creates any a memory pack failed to supply. `bare-local-opencode`
carries no consultant slates at all, so without the backfill it would produce a run with zero
consultants.

`.opencode/opencode.json` is read **without a git repo**, which matters because `/output` in the
container is not one.

opencode does **not** resolve `{file:}` through a symlinked directory — it uses the logical path. A
project root assembled with symlinks fails; apptainer bind mounts are real mounts, so the container
is unaffected.

## `OPENCODE_CONFIG` — the seam for per-run settings

`OPENCODE_CONFIG=/path/to.json` merges an extra config over the project's. Verified: the overlay's
`provider`, `model` and an absolute-path `{file:}` `apiKey` all land, while the project config's 46
agents, `permission` block and `instructions` survive untouched.

That is what keeps the endpoint out of the instance. The agent system is generated, tracked and
forked; the endpoint is a property of one launch and names a host that has no business in git. They
go in different files for that reason.

## Skills — Claude Code's tree is read directly

A project-level `.claude/skills/<name>/SKILL.md` **is discovered**, with its real path reported by
`opencode debug skill`. Global `~/.claude/skills/` and `~/.agents/skills/` are documented as
auto-loaded external skill roots.

- `skills.paths` in `opencode.json` registers additional roots explicitly and is scanned recursively
  for `**/SKILL.md`. Preferable to relying on the compatibility scan when the location is known.
- `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` and `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` switch the
  compatibility scan off. **A container must not set either.**
- Frontmatter needs `name` (lowercase-hyphenated, matching the folder) and `description`. A skill
  **without a description is filtered out and never surfaced** — silent, like the Codex case.

## Permissions — the default is the opposite of the other two CLIs

An unconfigured opencode resolves to:

```
*                     allow
doom_loop             ask
external_directory    ask
```

So shipping *no* permission block means shipping full auto-approval. To match the MadAgents posture
("the shipped system pre-approves nothing") the tree must ship an **explicit** block — the inverse of
the Codex rule, where the assertion is that nothing is granted.

A block mirroring what Claude Code actually prompts for resolves correctly (verified with
`opencode debug agent build`):

```json
"permission": {
  "read": "allow", "glob": "allow", "grep": "allow", "list": "allow",
  "task": "allow", "skill": "allow", "lsp": "allow", "todowrite": "allow",
  "edit": "ask", "bash": "ask", "webfetch": "ask", "websearch": "ask"
}
```

**Insertion order matters: the LAST matching rule wins.** Broad rules first, narrow rules last. The
built-in `*: allow` is emitted first, so an explicit block placed after it overrides — which is why
the above works.

Known keys: `read, edit, glob, grep, list, bash, task, external_directory, todowrite, question,
webfetch, websearch, lsp, doom_loop, skill`. Of these, `todowrite, question, webfetch, websearch,
doom_loop` take only a flat action, not a per-pattern object. Subagents resolve `question: deny` —
they cannot ask the user anything.

## Self-hosted providers

```json
"provider": { "local": {
  "npm": "@ai-sdk/openai-compatible",
  "options": { "baseURL": "http://host:8000/v1", "apiKey": "{file:/abs/path/token}" },
  "models": { "qwen3-32b": { "name": "Qwen3 32B" } }
}}
```

- Addressed as `local/qwen3-32b` — `<provider key>/<models key>` — via `--model` or the `model` key.
- **No npm install happens for this provider.** There is no `node`, `npm` or `bun` on this host, and
  a full request still succeeded: `@ai-sdk/openai-compatible` is bundled into the binary in 1.18.11.
  Nothing landed in `$XDG_CACHE_HOME/opencode/`. The `npm` key is still declared, and the docs'
  claim that packages install to a cache should be assumed true for *other* packages (plugins, other
  SDKs) — just not for this one.
- **`apiKey` may be omitted entirely.** A keyless endpoint completes a request. No placeholder secret
  needs inventing.

## Verified against a real model, in the container

Run on 2026-08-03 against a self-hosted `qwen3.6-27b`, through `./local/madrun.sh` and a real
Apptainer instance — not a stub. `opencode run <prompt> </dev/null` through the instance's
`run.sh` is the way to drive it non-interactively (argv is forwarded verbatim).

What that established:

- The lead loads `prompts/lead-discipline.md` **and** its slate through `instructions`, and can
  quote from both.
- The roster is visible to the lead, which names real consultants.
- **`task` dispatch works.** The log line to look for is
  `evaluated permission=task pattern=<agent> action=allow`, followed by
  `stream providerID=local modelID=… agent=<agent> mode=subagent`.
- **A dispatched consultant receives card + slate.** `opencode debug agent <name>` *inside the
  container* resolved `ma-physics-consultant` to 16,372 chars ending in its real wiki index.
- The `skill` tool loads skills straight out of `.claude/skills/`.

**One thing that is the model, not the harness.** A consultant with a ~16 KB prompt returned an
*empty* response — no error, no `finish_reason` complaint, just no text. The same dispatch to
`ma-physics-reviewer` (no slate, short prompt) answered correctly. On a thinking model the
reasoning tokens come out of the same budget as the answer, so a large always-loaded slate can
consume the whole reply. Diagnose it by checking the resolved prompt with `debug agent` first: if
the prompt is right, the harness is right.

**A real divergence from Claude Code, worth knowing before a slate grows.** Claude Code's
`memory: project` auto-load takes only the **first ~200 lines / 25 KB** of a slate. `{file:}`
interpolation has no such cap — it injects the whole file. Today every slate is well inside that
budget (`ma-wiki-write` targets ~80 lines), so the two agree; a slate that outgrows 25 KB would be
truncated on Claude Code and delivered whole on opencode. The finding above is why that matters:
uncapped is not automatically better.

## Offline behaviour — the remaining container risk

At startup opencode writes `$XDG_CACHE_HOME/opencode/models.json`, ~3.4 MB, fetched from the
models.dev catalogue over the network, plus an (initially empty) `bin/`. **Whether a session starts
cleanly with no network and no pre-populated cache is not yet established** — it is the one Phase 0
question a stub endpoint could not answer, because it is about reaching the *internet*, not the
model. Bind the host cache into the container and re-test on a node without egress.

## `websearch` is hidden unless you opt in

The tool list a session actually gets, verified by asking it:

```
bash, edit, glob, grep, read, skill, task, todowrite, webfetch, write
```

No `websearch`. opencode gates it: *"only available when using the OpenCode provider or when the
`OPENCODE_ENABLE_EXA` environment variable is set"*, and a self-hosted provider is neither. Set
`OPENCODE_ENABLE_WEBSEARCH=1` in `config.env` and the launcher passes `OPENCODE_ENABLE_EXA=1`
through; the list then gains `websearch`. `webfetch` is ungated and always present — but it only
retrieves a URL you already have, so it is not a substitute for search.

**It works, verified end-to-end from inside the container**: a real Exa search returned a real
`pdg.lbl.gov` URL and the top-quark pole mass. So the compute node here does have general egress,
and the keyless path needs no API key.

**Why it is nevertheless off by default.** The keyless path sends every query to Exa's hosted
service unauthenticated — a third party the operator has no contract with, which is usually what
self-hosting exists to avoid. It is rate-limited by an undocumented quota (opencode issue #15953
reports `Exa hit rate limit`), so a consultant that depends on it fails *intermittently*, which is
harder to diagnose than a tool that is plainly absent. And it needs internet egress a compute node
may not have.

**Who cares about this:** `ma-physics-consultant` and `ma-numerics-consultant` both instruct
verifying literature citations and PDG constants by web search rather than from recall. With the
flag off they find no such tool and fall back to recall — the exact failure those cards exist to
prevent. Neither state is free.

**It is also an `ask` permission**, so even with the flag on, a non-interactive run auto-rejects it
(`permission requested: websearch …; auto-rejecting`) — see the next section.

## Non-interactive runs auto-reject every `ask` permission

`opencode run` does not prompt. A permission resolved to `ask` is **rejected without asking**:

```
! permission requested: edit (.claude/agent-memory/<name>/MEMORY.md); auto-rejecting
✗ Edit … failed
Error: The user rejected permission to use this specific tool call.
```

Since the shipped block sets `edit: ask` (deliberately — the system pre-approves nothing), that
means **every slate write fails in a non-interactive run**, silently as far as the agent's own
narration goes. `/ma-wiki-write` will report success at the prose level and change nothing.

`--auto` ("auto-approve permissions that are not explicitly denied") is the escape hatch, and it is
opencode's analogue of Claude Code's `--dangerously-skip-permissions` and Codex's
`--dangerously-bypass-approvals-and-sandbox`. The Codex side of this repo already documents the
same shape — *"Under `codex exec`, a slate write fails instead of asking"* — so this is the
provider-consistent behaviour, not an opencode defect.

Interactively (the TUI, the normal user path) the prompt appears and the posture is the intended
one. It is unattended use — benchmark spawns, `run` invocations, anything scripted — that needs
`--auto`, and needs it consciously.

## Operational gotchas

- **`opencode run` blocks on an open stdin.** A non-interactive invocation must redirect
  (`< /dev/null`) or it hangs indefinitely with no output. This cost 2 minutes to diagnose and looks
  exactly like a model that never responds.
- `opencode.json` must be valid or opencode refuses to start — a hard fail, not a degraded start.
- Config is not hot-reloaded; any config-time change needs a restart.
- Escape hatches when a config is broken: `OPENCODE_DISABLE_PROJECT_CONFIG=1`, `OPENCODE_CONFIG=`,
  `OPENCODE_CONFIG_CONTENT=`, `OPENCODE_PURE=1`.

## Binary

Release asset `opencode-linux-x64.tar.gz` from `anomalyco/opencode` — a single ~171 MB executable.
**Dynamically linked** (unlike Codex's static-pie), but its floor is **glibc 2.17**, so binding the
host install into the container is safe for any realistic image.

The upstream `https://opencode.ai/install` script hardcodes `$HOME/.opencode/bin` and edits shell rc
files; it was deliberately not used. The tarball was extracted directly to a chosen prefix instead.
