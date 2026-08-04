---
description: The user-level `check` command end-to-end — do_check dispatch + check_check arg validation (parse/arg entry), the post-extract gates, the process_checks.py validators, AND the per-sub-check verification semantics (brs/gauge naming inversion, tolerances, real-ME-eval, BSM/loop availability). v3.7.1.
---

# check command: parse entry + validators + verification map (v3.7.1)

Source: dispatch in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` `do_check` (4065); validators in `$MADGRAPH_INSTALL/madgraph/various/process_checks.py`. **Part 1** = parse/arg entry (my slice core). **Part 2** = per-sub-check verification semantics (slice edge — I describe entry/dispatch; validator physics is deferred). Tolerances/thresholds are cited by `file:line` only — read the constant fresh at its coordinate (they drift across versions); this page keeps the coordinate + the tree-vs-loop relationship, not the number.

## `_check_opts` (madgraph_interface.py:2999, verbatim)
`['full','timing','stability','profile','permutation','gauge','lorentz','brs','cms']`. Default when `args[0]` not in this list: `'full'` inserted (check_check:1012).

---

# PART 1 — parse / arg entry

## do_check dispatch (4065)
- 4095 `check_check(args)` returns `param_card`.
- 4098-4103 **banner-as-param_card**: if the returned `param_card` is detected (`detect_card_type`) as a `'banner'`, it is treated as an event source — `options['events']=param_card`, real param_card extracted via `Banner(...).charge_card('param_card')`. So `check ... <banner.lhe>` pulls both momenta and parameters from the banner.
- 4108 `options['reuse'] = args[1]=='-reuse'`.
- 4112 for `stability`/`profile`: second arg is npoints (int).
- 4118+ `--energy --events --skip_evt --split_orders --helicity --reduction --collier_* --CTModeRun` option parsing.

## check_check (998) — the real validator (the 1988 one is Web-only override)
- 1001 requires a model; 1004 forbids v4 models (check is unavailable for v4 entirely).
- 1008 `<2` args and not `*options` → `InvalidCmd('"check" requires a process.')`.
- 1012-1014 if `args[0] not in self._check_opts` and not `args[0].lower().endswith('options')` → **inserts `'full'` at front of args**. **UNKNOWN type keyword is NOT silently misparsed and does NOT raise here** — `'full'` is prepended and the unknown word becomes the FIRST process-line token, failing LOUDLY downstream at particle resolution. Probe: `check lorentz_invariance e+ e- > mu+ mu-` → `InvalidCmd: No particle lorentz_invariance in model` (extract_process leg loop 5242). A mistyped check-type gives a "No particle X in model" error, never a silent wrong run. A common misconception is that a mistyped check-type silently misparses — in fact it fails loudly at particle resolution.
- 1017-1019 param_card auto-detected: for non stability/profile/timing types, if `args[1]` is a file → pop as param_card.
- 1029-1036 stability/profile: a default npoints (read the constant at check_check:1029-1036) inserted if not int.
- **1040 decay chains forbidden**: any `,` in a non-`--` arg → `InvalidCmd('Decay chains not allowed in check')`.
- 1043+ `user_options` defaults; cms/cmsoptions raise the check energy default (read at 1043+) and add `--cms --lambdaCMS --offshellness --recompute_width` defaults.

## Post-extract gates in do_check (4404-4436) — parse→validator boundary, in slice
- **4404-4407**: `proc_line = " ".join(args[1:])`; `myprocdef = self.extract_process(proc_line)` — the SAME parser as `generate`, BUT with `proc_number` left at default **0** (no `nb_proc` history-count). So `check` never auto-increments the process id. (Skipped when `args[0]=='cms'` and `--analyze!='None'` — re-analysis of a saved run, 4406.)
- **NLO_mode 'all'→'virt' (4412-4414)**: `if myprocdef.get('NLO_mode')=='all': set('NLO_mode','virt')` — only the virtual makes sense to check, so a bare `[QCD]` is downgraded to `virt`. (This is what lets permutation/lorentz/brs run on a loop process.)
- **timing/stability/profile require a loop process (4422-4425)**: `not myprocdef.get('perturbation_couplings')` → `InvalidCmd("Only loop processes can have their timings or stability checked.")` — these three demand a `[...]` perturbation bracket.
- **gauge requires QCD-only-or-tree + dual gauge (4427-4436)**: `gauge` with `perturbation_couplings not in [[],['QCD']]` → InvalidCmd (Feynman-vs-unitary only valid with no affected loop propagators); also `len(model.get('gauge')) < 2` → InvalidCmd (model must support both gauges).

## Validator dispatch sites in do_check
`check_timing` (4532), `check_stability` (4543), `check_profile` (4555), `check_unitary_feynman` (4583), `check_processes` (4598), `check_lorentz` (4611), `check_gauge` (4622), `check_complex_mass_scheme` (4670, the `cms` check). Each receives `myprocdef` + parsed `options`/`MLoptions`/`CMS_options` dicts.

## process_checks.py validators
- `MatrixElementEvaluator` (156): generic numerical-ME evaluator.
- `LoopMatrixElementEvaluator` (523) / `LoopMatrixElementTimer` (1057): NLO variants.
- Top-level checker fns: `check_profile` (2107), `check_stability` (2156), `check_timing` (2229), `check_processes` (2280), `check_gauge` (3060, + `check_gauge_process` 3147), `check_lorentz` (3326, + `check_lorentz_process` 3411), `check_unitary_feynman` (3516, the gauge-comparison driver), `check_complex_mass_scheme` (3632, + `check_complex_mass_scheme_process` 3874, the `cms` check).

## check option parser (do_check 4116-4373)
A back-to-front `while args[i].startswith('--')` loop parses `--energy --events --skip_evt --split_orders --helicity --reduction --collier_* --CTModeRun` (into `options`/`MLoptions`) and the CMS family `--offshellness --resonances --tweak --recompute_width --loop_filter --diff_lambda_power --lambda_plot_range --lambdaCMS --cms --analyze --show_plot --report --seed --name` (into `CMS_options`). Unknown `--opt` → `InvalidCmd("The option '%s' is not reckognized.")` (4370). `check options`/`check cmsoptions` (4375/4384) just print defaults and return. Per-option validation (eval'd lambdas, tweak `a->f(a,lambdaCMS)`) is check-internal; semantics deferred.

## Parse-vs-process boundary
do_check builds ProcessDefinitions via the same `generate` path then hands them to the validators. The *numerical/physics* meaning of each check (Part 2) is validator-internal, not parse-syntax.

---

# PART 2 — per-sub-check verification semantics

ALL sub-checks below **run a real numerical ME evaluation** (compile/run for loop, in-memory HELAS eval for tree) — none is static-only. `check` never writes a persistent process dir; it builds amplitudes + HELAS MEs in temp folders and cleans up (`clean_up` 2512, `clean_added_globals` 4786).

## Which validator each sub-check calls + what `full` runs (do_check 4531-4697)
| sub-check | validator (process_checks.py) | runs under `full`? |
|---|---|---|
| `permutation` | `check_processes` (2280) → `check_process` (2368) | YES (4597) |
| `lorentz` | `check_lorentz` (3326) → `check_lorentz_process` (3411) | YES (4609) |
| `brs` | `check_gauge` (3060) → `check_gauge_process` (3147) | YES (4621) |
| `gauge` | `check_unitary_feynman` (3516) | YES (4564, IF model has 2 gauges + pert∈[[],['QCD']]) |
| `cms` | `check_complex_mass_scheme` (3632) | **NO** — "slower… don't run automatically with 'full'" (4632-4633) |
| `timing` | `check_timing` (2229) | NO (loop-only) |
| `stability` | `check_stability` (2156) | NO (loop-only) |
| `profile` | `check_profile` (2107) = timing+stability | NO (loop-only) |

So **`full` = gauge + permutation + lorentz + brs** (NOT cms, NOT timing/stability/profile). Probe-confirmed: `check full e+ e- > mu+ mu-` → "4 check performed" (brs suppressed, see gate below).

## NAMING INVERSION (probe-confirmed, non-obvious) — `brs` vs `gauge`
- **`brs`** → `check_gauge` → logs **"Checking ward identities for …"**, columns `matrix | BRS | ratio | Result`. It is the **Ward/BRS identity** check: replaces a massless gauge-boson polarization with its momentum (`gauge_check=True`, 3203), checks ratio BRS/matrix ≈ 0. Probe `check brs e+ e- > a a`: ratio 3.77e-30 → Passed.
- **`gauge`** → `check_unitary_feynman` → logs **"Checking process … in unitary gauge / feynman gauge"**, columns `Unitary | Feynman | Relative diff | Result`. Re-extracts in BOTH gauges (do_set gauge Feynman/unitary, 4570-4577), compares |M|². Probe `check gauge e+ e- > a a`: rel.diff 0.0 → Passed.

So the user-facing names are counter-intuitive: "brs" is the ward-identity test, "gauge" is the unitary↔Feynman |M|² comparison. Don't infer from the name.

## Per-sub-check semantics + tolerance
### permutation (`check_process`, 2368)
- Generates the ME under **all leg permutations** (`itertools.permutations`, 2395); |M|² must be invariant. `quick=True` (always, do_check 4600) → one permutation per leg-position; loop processes capped at a small permutation count (read cap at 2415-2416). Tree dedup skips already-tested HelasMatrixElements (2467). Early-abort at a relative-spread cut (read at 2484-2487).
- **PASS tolerance (2501-2504): tree TIGHTER than loop** — `diff = 2·|max−min|/(|max|+|min|)`; read both threshold constants at 2501-2504. Reports via `output_comparisons` (2977).

### lorentz (`check_lorentz_process`, 3411)
- Evaluates |M|² at **lab frame** (`Original evaluation`, 3466) then under **boosts/rotations** — must be invariant. Tree (3473-3477): `for boost in range(1,4)` = boosts along x,y,z, each `boost_momenta(p, boost)` at the default boost β (read `beta` default in `boost_momenta`, 121). So tree = **lab + 3 boosts (along x/y/z)** = 4 frames. Loop (3478-3508): z-boost + π/2 + π/4 z-rotations only (boosts too imprecise without MadLoop improve_ps).
- **Formula (tree, 4946): `diff = (max−min)/abs(max)`; threshold at `output_lorentz_inv`:4908 (per-JAMP threshold 4988) — read the values.** Loop routes to `output_lorentz_inv_loop` (4841): **symmetrized formula `abs((ref−res)/((ref+res)/2))`** (4881), **two thresholds — `threshold_rotations` (4850), `threshold_boosts` (4854), the boost one looser** — selected by `'BOOST' in name` (4879); read both values. Returns `{'results':'pass'}` early (3468) → "Not checked" if m2 null. Probe `e+ e- > mu+ mu-`: rel.diff 2.56e-15 → Passed.

### brs / ward (`check_gauge_process`, 3147)
- **GATE (3152-3163): requires a massless spin-3 vector** (`spin==3 and mass=='zero'`). If absent → logs "No ward identity for …", returns None → **no Gauge-results block at all**. This is why `check full e+ e- > mu+ mu-` (no photon/gluon) emits NO brs block despite running 4 checks.
- ratio = |BRS m2| / |matrix m2| (output_gauge:3262). **threshold tree TIGHTER than loop** (read both at 3224-3227; per-JAMP threshold at 3302).

### gauge / unitary-feynman (`check_unitary_feynman`, 3516)
- **GATE (do_check 4564-4566): only runs if `len(model.get('gauge'))==2` AND `perturbation_couplings in [[],['QCD']]`.** If model lacks a 2nd gauge → silently not run under `full`; standalone `check gauge` with the same failing gate is rejected at the post-extract gate (4427-4436, Part 1).
- If no Goldstone after the gauge flip → `logger_check.error('No Goldstone present for this check!!')` (4582) but still runs. Reports via `output_unitary_feynman` (5013).
- **Formula (5069): `diff = (max−min)/abs(max)` over `[value_unit, value_feynm]`. Threshold HARDCODED at 5076 — the SAME for tree AND loop** (no `pert_coupl` split, unlike brs/lorentz/permutation which loosen for loops); read the value at 5076. Notably, gauge (unitary_feynman) is the one check whose main-m2 tolerance does NOT depend on tree-vs-loop. (Per-JAMP block 5090+ compares Unitary vs Feynman jamp sums, tree only — loop jamp list empty.)

### cms (`check_complex_mass_scheme`, 3632)
- Checks CMS consistency in the **off-shell region of detected s-channels**: varies `lambdaCMS` consistently with the width, verifies CMS−NWA difference is **higher order in λ**. Runs an NWA pass (`complex_mass_scheme False`, 3644) and a CMS pass. **Works at tree (LO counterpart) AND loop** — re-`extract_process`es `process_line` directly (3646) so decay chains forbidden (also blocked at check_check:1040). Warns if ≤4 external states (3669-3678) and if loop orders missing ("use [virt=all]", 3656-3666). **NOT run by `full`** (too slow). λ-expansion math deferred (cms is its own subsystem). **Note: cms is NOT NLO-only** — it runs against the LO counterpart too; missing loop orders only trigger a warning, not a rejection.
- **CMS option defaults** (set in check_check:1058-1074 when type is cms/cmsoptions): `--offshellness` (1065), `--lambdaCMS` (1072, a `(min-λ, points/decade)` pair), `--seed` (1074), `--cms=` default orders/rules `aewm1->…/lambdaCMS & as->…*lambdaCMS` (1059) — read each default at its cited line.
- **offshellness parse gate (do_check 4156-4160): must be `> -1.0`** — `offshellness<=-1.0` → InvalidCmd. **Semantics (process_checks.py:3981): `special_mass = (1.0+offshellness)*mass`** — sets the resonance INVARIANT MASS to `(1+X)·M`, i.e. `sqrt(p²)=(1+X)·M` ⟹ `p²=(1+X)²·M²`. A common misstatement is `p² > (X+1)·M²`; the factor is actually squared and it is an assignment of the probed point, not a `>` bound: `p² = (1+X)²·M²` (negative offshellness progressively scans, 4032-4037).

### timing / stability / profile (LOOP-ONLY)
- **GATE = the 4422-4425 post-extract gate (Part 1).**
- `check_timing` (2229): generates loop ME (`generate_loop_matrix_element`, 2013), times generation + MadLoop execution (`LoopMatrixElementTimer` 1057); `output_timings` (2897).
- `check_stability` (2156): evaluates loop ME over `nPoints` (default at check_check:1029-1036) random points, reports MadLoop accuracy distribution; `output_stability` (2560).
- `check_profile` (2107): timing THEN stability in one generation (no regen). All compile + run Fortran MadLoop → expensive; npoints is the 2nd positional arg (do_check 4112).

## Reporting / pager (do_check 4699-4783)
- "%i check performed in %s" (4700) — count = `nb_processes` across the sub-checks that ran.
- Footer note: tree non-cms → "Note That all width have been set to zero for those checks" (4711, probe-confirmed); cms → stable-final-state caveat (4704).
- Output paged via `pydoc.pager` if >20 lines and not `-reuse` (4769); else logged at info.

## BSM / loop availability summary
- **Tree BSM (any imported UFO model)**: permutation, lorentz, brs (if massless vector present), gauge (if model has 2 gauges), cms-LO — all available, tree tolerances above.
- **Loop processes (`[QCD]` etc.)**: permutation, lorentz, brs run with looser loop tolerances; gauge needs `pert∈[[],['QCD']]`; timing/stability/profile available ONLY here; cms available. Loop checks compile MadLoop → real Fortran run.
- **v4 models forbidden** for check entirely (check_check:1004).
