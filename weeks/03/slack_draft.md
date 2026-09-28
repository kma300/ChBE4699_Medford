Hi Dr. Medford, sorry for the slow reply, I was out visiting customer pilot plants last week. Answers to your questions:

1. Selection: greedy D-optimal design. From the 464 MOFs that respond at all, I added one MOF at a time to maximize the log-determinant of the noise-weighted Fisher information (the 12x8 response matrix projected onto the 7 independent composition directions, since fractions sum to 1), then did one-for-one swaps until nothing improved.
2. Simulation: each MOF's signal is its Henry coefficients times the mole fractions (dilute limit), plus Gaussian noise at 1% of that MOF's full-scale response (with a small floor). I recover the composition with exact nonnegative, sum-to-one least squares and score 1,000 held-out mixtures (all 8 gases, 2-7 gas subsets, and ethane/ethylene and propane/propylene ratio sweeps). Designs are picked on a separate development set.

This week I tried both of your suggestions (slides attached):
- GA over 12 of 464 MOFs (about 1.8 x 10^23 combinations): ethylene error went from 9.91 to 9.53 pp on held-out mixtures and held up on a fresh set. But even all 464 MOFs at once only reach 8.55 pp, so at 1% noise the limit looks like signal rather than search.
- Gradient map: the error hinges on the ethane/ethylene contrast of a few MOFs (mostly GEHSAN). In D-MOPH, ethane outadsorbs ethylene in 87% of MOFs (median ratio 0.50), and the MOFs that favor ethylene barely adsorb. Steering the selection with a linearized gradient did worse than the GA, so next I'd differentiate the actual constrained solver.
- Ethylene only reaches my 2 pp target at about 0.05% noise.

Question: what noise level is realistic for MOF sensors? That decides whether I keep pushing the ethylene/ethane ratio or treat ethane and ethylene as one signal and prune toward 4-6 MOFs before the midterm.
