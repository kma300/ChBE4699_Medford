# Reproducing the approved Week 2 benchmark

This package contains the deterministic benchmark script, frozen protocol, full result tables, source-coefficient subset, validation and scientific figures. It contains synthetic outputs, not experimentally measured mixtures.

The original deposit is available at https://zenodo.org/records/16754752 . The script reads the local final.csv path recorded in protocol/data provenance. That source file must have SHA-256 a748213897204191619a43c6d6c08f80e8109b943e936233a1a0bf9e96f5d938.

Runtime versions are recorded in protocol_frozen.json; SciPy is used only for an independent validation. Matplotlib is used by write_results.py for figures. Paths in the scripts refer to this local workspace. To reproduce elsewhere, adapt ROOT and SOURCE, create work/medford-array and outputs/medford-array, and generate a new freeze manifest before final evaluation. Keep prior outputs in a separate directory.

Run benchmark.py stages in this order: prepare, validate, development, freeze, final. Then run write_results.py. The final stage checks that the analysis script matches its frozen hash. Set OPENBLAS_NUM_THREADS=1 and VECLIB_MAXIMUM_THREADS=1 for reproducible single-threaded linear algebra. Development and final seeds are fixed; rerunning them is reproduction, not a new held-out evaluation.

The 471x8 source subset is included for inspection. The analysis uses directly computed values only, no imputation and no post-test tuning. Fractions and errors refer to the normalized eight-gas system. Definitions, limitations and detailed results appear in research_results.md and protocol_frozen.json.
