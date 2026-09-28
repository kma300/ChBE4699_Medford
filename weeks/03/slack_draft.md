Hi Dr. Medford, sorry for the slow reply, I was out visiting customer pilot plants last week. The week 3 one-pager is attached, including answers to your two questions: selection was greedy D-optimal design plus one-for-one swaps, and detection is simulated as a linear Henry's-law response with 1% noise, inverted by nonnegative, sum-to-one least squares on 1,000 held-out mixtures.

TL;DR:
- Your GA suggestion helped a little: ethylene error 9.91 to 9.53 pp (104,405 arrays scored).
- Even all 464 MOFs together only reach 8.55 pp, so ethylene/ethane is limited by signal, not by the search.
- Your gradient idea shows why: the error hinges on ethane-vs-ethylene contrast, and in D-MOPH ethane outadsorbs ethylene in 87% of MOFs.
- A 2 pp ethylene target would need about 0.05% sensor noise.

Question: what noise level is realistic for MOF sensors? That decides whether we keep pushing the ratio or lump ethane and ethylene and prune toward 4-6 MOFs before the midterm.
