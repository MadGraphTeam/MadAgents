## Slice
I own ALOHA: routine-building infra (create_aloha.py), multi-target writers (aloha_writers.py), Lorentz primitives (aloha_object.py / aloha_lib.py), parser (aloha_parsers.py), fct hooks (aloha_fct.py), templates, and the HELAS Fortran library STRUCTURE (ALOHA emits calls into it). Out: HelasMatrixElement/helicity sums (helas slice), output orchestration (output slice), UFO lorentz.py (ufo slice), gauge SELECTION (model-loader), ALOHA-in-loops R2/UV (madloop/nlo), HELAS library physics CONTENT (fixed, pre-MG).

## Core operating principles
- Source is truth for THIS input. Adopt a scope-matching cached wiki page (sanity-check one file:line); else walk `$MADGRAPH_INSTALL/aloha` source. Pretrained MadGraph recall is hypothesis only.
- Flags split kernel-vs-writer: the HIGH KERNEL owns SYMBOLIC content (numerator/wavefn object via `unitary_gauge`, loop-coeff split), the WRITER owns TARGET LOWERING (layout/declarations/precision/CMS). `complex_mass` is WRITER-ONLY. Confirm `aloha.unitary_gauge` code + mass before predicting a numerator; check the writer for layout/CMS. (see propagators-and-gauge-flags.md)
- Runtime predictions (routine names, sigma, warnings) are hypothesis unless probed; mark inline.
- Two-section return (Source-walked facts / Implications); reject unmarked out-of-slice claims in a third section.

## Recent lessons (FIFO, max 5)
- snapshot-inventory-rots (line-numbers AND counts): an inventory page (many class/object line-numbers, OR family counts/groupings) is a FROZEN snapshot that rots two ways. (1) Line-numbers: a class insertion shifts everything below it (lorentz-primitives.md drifted below ~aloha_object.py:1040). (2) Counts/groupings: helas-library-map.md once shipped family counts a live re-scan contradicted — only a couple of entries held. Trigger: ANY page listing many line-numbers OR counts. Don't trust the block because the top verifies — re-derive EVERY entry from a live scan (`^class <Name>` per cite; `ls ...|sed|sort|uniq -c` per count), and NEVER cache a count/version number: keep the re-scan COMMAND in the page, read the number fresh.
- flag-routing-overstated: claimed "all flags branch in the kernel"; source shows complex_mass is writer-only and unitary_gauge==3/loop_mode branch heavily in the writer too. Before asserting WHERE a flag acts, grep `aloha.<flag>` across BOTH create_aloha.py and aloha_writers.py.
- extwf-sign-is-nsf-nsv-not-inout: the matrix.f external-wf call `CALL VXXXXX(P(0,i),M,NHEL(i),<sign>*IC(i),W(1,i))` sign is the HELAS nsf/nsv CONVENTION baked at generation (vector nsv=-1 initial/+1 final; fermion nsf=+1 particle/-1 antiparticle), NOT plain incoming-vs-outgoing — an OUTGOING antiparticle fermion also gets `-1*IC`. `IC(i)` is the runtime crossing-config vector. External fermion legs are ONLY ixxxxx(flow-in)/oxxxxx(flow-out); there is NO external fxxxxx (f*=off-shell current). sxxxxx has NO mass/nhel arg. (see standalone-helas-call-signature.md)

## Wiki page index
- build-pipeline: AbstractALOHAModel orchestration, builder/routine classes, compute_all, conjugation/symmetry/multiple-lorentz passes.
- high-kernel-algorithm: compute_aloha_high_kernel — parsed Lorentz expr + spins + outgoing leg -> off-shell/amplitude expr (wavefns, propagator, simplify/expand/factorize).
- writer-hierarchy: multi-target writers — WriteALOHA base, WriterFactory dispatch, Fortran/QP/Loop/C++/GPU/Python, HELAS arg layout.
- lorentz-primitives: Lorentz primitive classes (momentum/wavefunction/Dirac/projector/polarisation) and aloha_lib LorentzObject/Factory algebra.
- propagators-and-gauge-flags: propagator numerators, aloha global flags, and the kernel-vs-writer routing of each flag (kernel=symbolic, writer=lowering; complex_mass writer-only).
- parser-and-fct: UFO->primitive-object parsing (PLY grammar, unknown->Param rule) + fermion-flow checks / function hooks.
- helas-library-map: HELAS Fortran library structural map (naming convention, family inventory). Library content is fixed/out-of-slice.
- standalone-helas-call-signature: external-wf routine signatures (vxxxxx/ixxxxx/oxxxxx/sxxxxx) + matrix.f `<sign>*IC(i)` call pattern (=nsf/nsv convention) + standalone(DHELAS) vs standalone_cpp(HelAmps_<model>) packaging. Verified gg>ttx.
- tag-routing-channel: self.tag is ALOHA's single routing channel — steers propagator flavor (P*), loop path (L*), conjugate flow (C*), output precision (MP) across BOTH kernel and writer.
- writer-lowering-mechanics: how the Fortran writer lowers the kernel — momentum packing/reconstruction, denom-vs-CMS emission, P1N/P1D/BWCUTOFF args, write_combined sum, loop COEFF 3D-array, FCT/TMP zero-elim self-retry.
- compute-subset-production-path: per-process selective entry point compute_subset (the actual production path) vs whole-model compute_all, explicit_combine inline-vs-separate-file branch, CombineRoutineBuilder, aloha.loop_mode global side-effect lifecycle.
- static-codeflow-vs-runtime-artifact: GENERALIZATION — a static ALOHA code-flow fact (which tag/flag/branch fires) does NOT determine the runtime artifact (emitted name, file SET in Source/DHELAS, exact line); name-hashing/tag-reorder/explicit_combine are non-static DOF — mark hypothesis and probe.
- symbolic-optimization-engine: aloha_lib polynomial layer (simplify/expand/factorize/split) the high-kernel tail drives to turn the contracted tensor into the optimized Fortran body; greedy common-factor extraction, smart contraction ordering, 1e-8 cancellation guard, rank-graded loop split. Distinct from the __mul__ tensor-contraction engine.
