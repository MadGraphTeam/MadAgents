---
description: NLO/aMC@NLO Delphes path — aMCatNLOCmd inherits do_delphes but overrides check_delphes with a STDHEP-only glob-and-gunzip resolver (no HepMC); run_delphes3 absent from NLO template
---

# Delphes on the NLO (aMC@NLO) path

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. NLO is normally
another slice's territory, but the Delphes handoff on the NLO path is mine and it
differs from the LO path.

## Inheritance structure
- `aMCatNLOCmd` (line 1474) inherits `common_run.CommonRunCmd`
  (`class aMCatNLOCmd(CmdExtended, HelpToCmd, CompleteForCmd, common_run.CommonRunCmd)`).
- It overrides ONLY `check_pgs` (492) and `check_delphes` (550) — NOT `do_delphes`
  / `do_pgs` (grep: no `def do_delphes`/`def do_pgs` in the file). So the NLO path
  executes the SAME `do_delphes` body as LO (common_run_interface.py:3367), including
  `prog='../bin/internal/run_delphes3'` and the delphes2-vs-3 `data/`-dir detection.

## NLO `check_delphes` is a different input resolver (550-605)
Unlike the LO `check_delphes` paths-list (see check_delphes-input-resolution page),
the NLO version is **STDHEP-only and glob-based**:
- delphes_path guard identical in spirit (557-565), error text `'No valid delphes
  path set.'` (note: no `\n`, unlike LO's).
- No-arg case requires `Events/pythia_events.hep` to already exist (582-585) else
  `InvalidCmd('No file pythia_events.hep currently available...')`.
- One-arg case: `misc.glob('events_*.hep.gz', Events/)` (589), takes `filenames[0]`
  (597), gunzips it to `Events/pythia_events.hep` via `cluster.asyncrone_launch('gunzip'
  ...)` (598-601). Returns nothing (the inherited do_delphes re-resolves via its own
  check_delphes? NO — do_delphes calls `self.check_delphes` which is THIS override).
- **No HepMC handling at all** — only `.hep` (STDHEP). Different from LO check_delphes,
  which prioritizes `_pythia8_events.hepmc[.gz]`. The NLO override predates / ignores the
  Pythia8-HepMC branch.

## Caution — signature mismatch (static source fact, runtime PROBE)
- Inherited `do_delphes` calls `self.check_delphes(args, nodefault=no_default)`
  (common_run_interface.py:3383, keyword arg). The NLO override signature is
  `check_delphes(self, arg)` (amcatnlo_run_interface.py:550) — **no `nodefault`
  parameter** (same for the NLO `check_pgs(self, arg)` at 492 vs LO `check_pgs(self, arg,
  no_default=False)`). Calling the inherited do_delphes on an aMCatNLOCmd instance would
  raise `TypeError: check_delphes() got an unexpected keyword argument 'nodefault'`.
  This is a STATIC source fact (signatures verified, v3.7.1). Whether it actually fires
  depends on whether the NLO laststep dispatch reaches the inherited do_delphes — PROBE
  before asserting NLO+Delphes runs at all. If a separate NLO dispatch calls check_delphes
  WITHOUT the kwarg, the mismatch is dormant. Either way: do not assume the LO Delphes
  flow transplants cleanly onto NLO.

## Caution — run_delphes3 absent from the NLO template (CONFIRMED filesystem fact)
- `do_delphes` is inherited and points at `../bin/internal/run_delphes3`, but the LO
  wrapper script `run_delphes3` lives in `Template/LO/bin/internal/` and there is NO
  `Template/NLO/bin/internal/run_delphes*` — CONFIRMED (v3.7.1) directly by
  `find Template/NLO -name 'run_delphes*'` → empty AND `ls Template/NLO/bin/internal/ | grep
  delphes` → empty. This is a plain filesystem fact (no MadGraph run needed), upgraded from
  the earlier "RUNTIME/probe-candidate" framing. So an NLO proc dir built from the NLO
  template does NOT ship a usable `bin/internal/run_delphes3`; the inherited do_delphes launch
  (`prog='../bin/internal/run_delphes3'`) would fail at the wrapper (missing prog / "No Delphes
  executable found" only reached if the script existed). The one thing still genuinely runtime
  is whether some other copy mechanism injects the LO wrapper into an NLO dir — not observed in
  the template tree.
- The NLO check_delphes return value is None (no explicit return of filepath like LO's
  411) — the gunzipped `Events/pythia_events.hep` becomes the de-facto fixed input,
  matching the legacy fixed-name fallbacks. The inherited do_delphes uses `filepath`
  from `check_delphes`; on the NLO override that is None, so do_delphes line 3384
  (`if no_default and not filepath`) and the `filepath` arg to run_delphes3 behave
  differently than LO — PROBE-candidate to confirm the actual filepath handed to the
  wrapper on an NLO run.
  - STATIC refinement (read common_run_interface.py:3384-3385, v3.7.1): the branch is
    `if no_default and not filepath: return`. So filepath=None DIVERGES by how do_delphes
    was called: (a) `delphes --no_default` (no_default=True) → `not None` True → do_delphes
    RETURNS at 3385 before any launch (silent no-op); (b) explicit `delphes` command
    (no_default=False) → branch skipped → None flows as the `$5` filepath arg into
    run_delphes3, whose extension test `${file: -3}` on an empty string mis-dispatches
    (likely the else/HepMC branch with a missing file). Since NLO does NOT auto-chain
    (no shower tail-call — see delphes-trigger-chain-from-shower-step page), the no_default
    early-return path (a) is NOT the one an NLO user hits; an explicit NLO `delphes` would
    take path (b). Still PROBE the actual filepath, but the divergence itself is now a
    static fact, not a guess.
  - Probe-confirmed (v3.7.1): path
    (b) does NOT reach run_delphes3 at all. It crashes earlier, in the launcher, with a
    Python `TypeError` — because the launch arg list is NOT stringified via `str()`. It is NOT
    the case that `filepath=None` becomes the shell string `"None"` and the wrapper falls
    to its `else` → `DelphesHepMC2 ... None`. Chain:
    * do_delphes (common_run_interface.py:3433) calls
      `clus.launch_and_wait(prog, argument=[delphes_dir, run, tag, str(cross), filepath], ...)`.
      Note ONLY `cross` is wrapped in `str()`; `filepath` is passed raw. With filepath=None the
      list is `[..., '<cross>', None]`.
    * default path: `not self.cluster` → `clus = cluster.onecore` (3429-3430).
      `onecore = MultiCore(1)` (cluster.py:2512). `MultiCore.launch_and_wait` (cluster.py:815-822)
      does `return misc.call([prog] + argument, ...)`; `misc.call` (misc.py:982) → bare
      `subprocess.call(arg, ...)` — NO `str()` map over the list.
    * PROBE: `subprocess.call(['/bin/echo','ddir','run','tag','1.23',None])`
      → `TypeError: expected str, bytes or os.PathLike object, not NoneType`. subprocess does
      NOT coerce None to "None". So the default (onecore) launch raises a TypeError before any
      Delphes binary is invoked.
    * real-cluster path: a configured backend (e.g. PBSCluster.submit, cluster.py:~1394) builds
      the job script via `text += ' ' + ' '.join(argument)`. `' '.join([...,None])` also raises
      `TypeError: sequence item 4: expected str instance, NoneType found`. So the cluster path
      ALSO crashes in Python, never emitting a `None` token to the shell.
    * Net: explicit NLO `delphes` (no_default=False, filepath=None) does NOT silently no-op and
      does NOT run the HepMC2 binary on a bogus `None` file. It raises a TypeError in the launcher
      (onecore→subprocess, or cluster→`' '.join`). The `str(cross)` element being the ONLY
      explicitly stringified arg is exactly why the unstringified None is fatal. The trap: assuming
      list-arg stringification happens — it does for `cross` only.
