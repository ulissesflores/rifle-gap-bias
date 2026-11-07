# Specification of the test and the mechanism

This document describes, in formal notation, what `code/rifle_ado.py` computes: the Python
translation of the default path of `rifle.ado` (Berry & Fowler, 2018), with and without gap
stitching, and the argument of Section 3.2 of the paper on why stitching shifts the test. The
measured numbers are in `output/results.json` and in Table 1 of the paper; here there are only
definitions.

## 1. Notation

| Symbol | Meaning |
|---|---|
| $m$ | unit (municipality) |
| $t$ | calendar period, $t = 1, \dots, T$ |
| $y_{mt}$ | outcome; missing when the cell is not observed |
| $\ell_{mt}$ | leader identity (in the paper, the municipality-person pair) |
| $O$ | set of observed cells |

## 2. The test, step by step

The lines cited are those of the `rifle.ado` distributed on SSC; the same reference is annotated
in the code.

1. **Period residual** (l.33-37). Over the observed cells,
   $\tilde y_{mt} = y_{mt} - \bar y_{\cdot t}$, with $\bar y_{\cdot t}$ the mean of period $t$ in $O$.
2. **Global leader identity** (l.41-47). Each leader receives a single index across all
   units; missing cells leave the sample.
3. **Unit time.**
   - With stitching (default, l.49-56): the observed periods of each unit are renumbered
     $1, \dots, n_m$, and the period after a gap becomes adjacent to the period before it.
   - With `nostitch` (l.58-76): each stretch of consecutive observed periods becomes a unit
     of its own; a stretch with two or more rows and a single leader is dropped; a one-row
     stretch stays.
4. **Stints** (l.88-92). A stint is a maximal sequence of rows of the same unit with the same
   leader, in the order of the renumbered time. With stitching, the same person on both sides
   of a gap forms a single stint.
5. **Statistic** (l.83). For a partition $G$ of the rows into groups $g$ of size $n_g$,

   $$R^2(G) = \frac{\sum_{g} n_g^{-1}\left(\sum_{i \in g} \tilde y_i\right)^2 - N^{-1}\left(\sum_i \tilde y_i\right)^2}{\sum_i \left(\tilde y_i - \bar{\tilde y}\right)^2}.$$

   In the real partition the groups are the leader identities (`absorb(leader)`): the same
   person in two stints forms one group.
6. **Permutation** (l.103-120). Within each unit, the order of the stints is drawn at random,
   keeping the length of each one, and the leader identity of each stint is placed back in the
   new positions. $R^2$ of the drawn partition is computed.
7. **Decision** (l.142-158). With $B$ draws, the p-value is
   $p = B^{-1} \#\{b : R^2_b > R^2_{\mathrm{real}}\}$ (strictly greater), and the difference
   reported by the package is $R^2_{\mathrm{real}}$ minus the mean that includes the real row
   itself, $(R^2_{\mathrm{real}} + \sum_b R^2_b)/(B + 1)$.

The translation does not implement the options `controls`, `growth` and `notrend`, and assumes
that only the outcome has missing values. The tests `tests/test_rifle_ado_mao.py` (hand
calculations) and `tests/test_rifle_ado_ponta.py` (exact enumeration of the orderings) check
steps 3 to 7.

## 3. Why stitching shifts the test

The denominator of $R^2$ is the same in all permutations of a dataset, and so is the term
$N^{-1}(\sum_i \tilde y_i)^2$. Ranking $R^2$ is therefore equivalent to ranking

$$Q(G) = \sum_{g} \frac{1}{n_g}\left(\sum_{t \in g} y_t\right)^2 .$$

Under the null, with $y$ stationary autoregressive in **calendar** time, with variance
$\mathrm{\sigma}^2$ and covariance $\mathrm{\sigma}^2\mathrm{\rho}^{|t-s|}$,

$$\mathrm{E}[Q(G)] = \sum_{g} \frac{1}{n_g} \sum_{t, s \in g} \mathrm{\sigma}^2 \mathrm{\rho}^{|t-s|}.$$

Stitching changes the time index, not the covariance: two spliced periods remain
$|t - s|$ calendar periods apart. The real groups never cross the gap that separates two
leaders; the drawn ones do. The group that contains the gap has less internal covariance, and
for that reason the real fit is favored even without a leader effect. The sign depends on where
the gap falls relative to the boundaries of the real and drawn groups: Section 3.2 of the paper
derives four cases with six periods (equations 3 to 6), two in which the mean difference favors
the real fit and two in which it favors the draw. The rejection rates do not come from these
calculations; they were measured by simulation (Section 5 of the paper and
`output/results.json`).

With `nostitch`, no drawn group crosses the gap, because each stretch is drawn separately. The
link that remains is that of the same person in the two stretches, who stays in a single group
(step 2); it leaves a residual covariance of order $\mathrm{\rho}^2$ between the two sides of
the gap (Section 6.1 of the paper).

## Reference

Berry, C. R., & Fowler, A. (2018). *RIFLE: Stata module to perform randomization inference for
leader effects* (Statistical Software Components S458461). Boston College Department of
Economics. https://ideas.repec.org/c/boc/bocode/s458461.html
