# Container mode — deferred

The shipped installer is **bare only** (the agent runs directly in the user's repo). Container
mode (wrapping the repo in an Apptainer sandbox at its real host path) was built and validated
but is **not exposed in the skills** yet, to keep the first release simple.

Nothing was deleted — the container implementation is preserved and dormant:

- **`templates/start_madagents.container.sh`** — the container launcher (Apptainer bind+launch,
  arg/env forwarding, host-claude-auth bind). Unused by the bare skill.
- **`<!-- container-only -->` blocks + `{{REPO}}` placeholder** in the templates — these carry
  the container environment description (`/workspace`, `/opt`, repo-at-real-path). The bare
  render **strips them**, so they are inert for bare installs but ready for container.
- **`scripts/render.sh`** still has a `container` branch (keeps the blocks, substitutes
  `{{REPO}}`/`{{DOCS}}=/madgraph_docs`, bakes `{{IMAGE}}`). The bare skill only calls the
  `bare` branch.
- **`examples/verify_install.sh`** still has `container`-mode checks (only run when invoked
  with `container`).

## Re-enabling later

The renderer, templates, and verifier already support container. To bring it back, restore the
container path in the two skills (recoverable from git history):

1. `install-madagents`: re-add the **mode** choice, the **container setup** step (Apptainer
   check / unprivileged install, image reuse-or-build via `image/create_image.sh`, per-repo
   `overlay.img` created **without** `--fakeroot`), the `container` render call
   (`render.sh ... container /madgraph_docs "$TARGET" "$IMAGE"`), distribution of the baked
   container launcher, the `image_variant`/`image_path` manifest fields, and the `.gitignore`
   overlay note.
2. `update-madagents`: re-add the `container` render case (base + new) using the manifest's
   `mode`/`image_path`/`target`.

See the project's earlier history for the exact bash that was already validated.
