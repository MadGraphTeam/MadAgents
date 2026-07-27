---
description: What MG5_aMC actually checks/requires at startup vs at install/compile time — Python 3.7 hard exit, six, py3.9 warning; compilers deferred; NLO loop-libs auto-installed at runtime (v3.7.1).
---

# Prerequisites & startup checks (what MG5 enforces, and when)

MG5 enforces very little at startup; most commonly-listed prerequisites are needed only later, at install / output / compile / launch time.

## Enforced at interpreter startup — `bin/mg5_aMC`
- **Python 3.7 hard floor** `:26-28`: `if sys.version_info < (3, 7): sys.exit('MadGraph5_aMC@NLO works with python 3.7 or higher.')`. This is the ONLY hard version gate. Python 2 is not specially "deprecated" by any check — it simply fails the `< (3,7)` exit.
- **Python 3.9-and-below WARNING (not fatal)** `:29-30`: logs "Support for Python3.9 (and below) has been dropped since end of 2025 … Continue at your own risk". Run continues.
- **`six` module REQUIRED** `:34-40`: `import six` failure → `sys.exit(message)` telling user to `pip install six`. This is an easily-overlooked hard startup prerequisite.
- **py3.12+ reweight advisory** `:97-98` (warning only); readline optional `:100-135` (tab-completion degrades, no exit).
- The shipped interpreter is whatever the launcher's shebang (line 1) names — read it; it is an environment-specific venv, not the system python3.

## NOT checked at startup — deferred
- **No Fortran/C++/make check at startup.** The Fortran compiler is resolved lazily inside `do_install` FC-resolution (`madgraph_interface.py:6731-6753`: honours `$FC`, else `options['fortran_compiler']`, else `gfortran`, else `g77`, else raises "Require g77 or Gfortran") and again at output/compile time. g++ is needed only for C++-emitting tools (Pythia8/Delphes) at their build. So gfortran / g++ / GNU make are real dependencies but enforced at build time, not at launch.
- **INSTALL file** ($MADGRAPH_INSTALL/INSTALL) lists the intended deps: Python 3.7+, bash, perl 5.8+, a Fortran 77 compiler (g77/gfortran), a c++ compiler; and states verbatim: "other dependencies (for loop) will be installed at run time the first time that you need it." This is documentation, not an enforced check.

## NLO loop libraries — "handled automatically", with nuance
Loop reduction libraries (CutTools/IREGI bundled; Ninja/Collier/Golem/oneloop) are installed on first NLO need via the AskLoopInstaller menu (see `reduction-library-install-menu.md`) — but note it is a MENU with defaults, not fully silent, and "online" default is hardcoded True while local install is never auto. CutTools+IREGI ship in `vendor/` (offline path, see `vendor-and-offline-install.md`). So "handled automatically" is a fair summary; the nuance is menu-with-defaults + vendor-bundled cores.

## Cautions
- `six` is the prerequisite most likely to bite and is easily overlooked.
- The `-O` relaunch (`bin/mg5_aMC:74-82`, `__debug__ and not options.debug`) re-execs the interpreter in optimize mode by default — orthogonal to prereqs but means `__debug__` is False in a normal run (see `debug-flag-release-behavior.md`).
