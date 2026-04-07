# 24 — Biased Event Generation

Biased event generation allows efficient sampling of phase-space regions that would normally be poorly populated, such as high-pT tails or high-mass regions. The bias enhances the probability of generating events in the target region while adjusting event weights to preserve the correct physical distributions.

## Contents

- [When to Use Biased Generation](#when-to-use-biased-generation)
- [Run Card Configuration](#run-card-configuration)
  - [The `bias_module` Parameter](#the-bias_module-parameter)
  - [The `bias_parameters` Parameter](#the-bias_parameters-parameter)
- [Built-In Module: `ptj_bias`](#built-in-module-ptj_bias)
  - [Parameters](#parameters)
  - [Example: Enhanced High-pT Jets](#example-enhanced-high-pt-jets)
- [Important: Weighted Events](#important-weighted-events)
- [Writing Custom Bias Modules](#writing-custom-bias-modules)

## When to Use Biased Generation

Standard (unbiased) event generation produces events proportional to the differential cross-section. For steeply falling distributions (e.g., jet pT spectra), this means very few events populate the high-pT tail. To study these tails with adequate statistics, you would need to generate an impractically large number of events.

Biased generation solves this by over-sampling the tail region and assigning lower weights to the enhanced events, so that weighted distributions remain correct.

## Run Card Configuration

```
None  = bias_module       ! Bias module: None, ptj_bias, or path to custom module
{}    = bias_parameters   ! Parameters passed to the bias module
```

### The `bias_module` Parameter

| Value | Description |
|-------|-------------|
| `None` | No bias (default). Standard unbiased generation. |
| `ptj_bias` | Built-in module that enhances the high-pT tail of the leading jet. |
| `<path>` | Path to a custom bias module directory. |

### The `bias_parameters` Parameter

A dictionary of parameters passed to the bias module. The exact parameters depend on the module. Format:

```
{ptj_bias_target_ptj: 1000.0, ptj_bias_enhancement_power: 4.0}  = bias_parameters
```

## Built-In Module: `ptj_bias`

The `ptj_bias` module enhances the high-pT region of the leading jet. The bias weight is:

```
bias_weight = (max_ptj / ptj_bias_target_ptj) ^ ptj_bias_enhancement_power
```

where `max_ptj` is the transverse momentum of the hardest jet in the event.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ptj_bias_target_ptj` | 1000.0 | Target pT value (GeV). Events near this pT are enhanced. |
| `ptj_bias_enhancement_power` | 4.0 | Power of the enhancement. Higher values give stronger bias toward high pT. |

### Example: Enhanced High-pT Jets

```
import model sm
generate p p > j j
output dijet_highpt
launch dijet_highpt
  set run_card bias_module ptj_bias
  set run_card bias_parameters {ptj_bias_target_ptj: 500.0, ptj_bias_enhancement_power: 4.0}
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  done
```

This generates 50,000 events with enhanced statistics in the high-pT jet region around 500 GeV.

## Important: Weighted Events

When using biased generation, events carry non-uniform weights. The event weight in the LHE file includes the inverse of the bias factor, so that:

```
physical_weight = event_weight (which already includes 1/bias_weight correction)
```

The `ptj_bias` module sets `impact_xsec = False`, meaning the total cross-section reported by MG5 is the **unbiased** physical cross-section. The bias only affects the distribution of events in phase space, not the total rate.

When filling histograms, you **must** use event weights. Unweighted histograms will show the biased (enhanced) distribution, not the physical one.

## Writing Custom Bias Modules

Custom bias modules are Fortran files placed in a directory. The module must define a subroutine `bias_wgt(p, original_weight, bias_weight)`:

```fortran
subroutine bias_wgt(p, original_weight, bias_weight)
    implicit none
    include '../../maxparticles.inc'
    include '../../nexternal.inc'
    double precision p(0:3,nexternal)
    double precision original_weight, bias_weight

    ! Common block (mandatory)
    double precision stored_bias_weight
    data stored_bias_weight/1.0d0/
    logical impact_xsec, requires_full_event_info
    data impact_xsec/.False./
    data requires_full_event_info/.False./
    common/bias/stored_bias_weight,impact_xsec,requires_full_event_info

    ! Your bias logic here
    bias_weight = ...

    return
end subroutine bias_wgt
```

The directory must also contain a `makefile` for compilation. Place the directory under `<PROC_DIR>/Source/BIAS/` or specify the full path in `bias_module`.

Key flags in the common block:
- `impact_xsec`: If `.True.`, the bias affects the reported cross-section. If `.False.` (recommended), the cross-section is unbiased.
- `requires_full_event_info`: If `.True.`, the full event information (color, helicities) is available in `p`. Usually `.False.` is sufficient.
