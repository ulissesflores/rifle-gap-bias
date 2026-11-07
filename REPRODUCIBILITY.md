# Reproducibility

This package follows the lab's two-seal contract: **reproducible derivation** (what is redone here, from scratch,
with the same result) and **frozen evidence** (what is not redone here, but has its sha256 pinned and checked).
Code comments, test names, script messages, the preregistration (a dated document), the frozen outputs and the
origin hash chains are in Portuguese and stay as recorded: translating them would rewrite sealed evidence.

## Seal 1 — reproducible derivation

### Light path (`python run_all.py`, minutes)

1. `scripts/verify_chain.py` recomputes the provenance chain of the latest run in `runs/` and exits with the number
   of discrepancies (0 = intact).
2. `pytest`: every number anchored in the four editions of the paper (exported to `data/numeros_publicados.json`)
   against `output/results.json` and present in the DOCX of each edition; no malformed anchor;
   `output/results.json` rebuilt byte for byte; the port of `rifle.ado` against hand calculations, against the
   exact enumeration of orderings (with and without `nostitch`) and against an independent reconstruction of the
   mean that includes the real row; absence of CPF and structure of the panel; linkage of the origin study's
   chains and registration of the frozen outputs; determinism of a small cell.
3. `code/montar_results.py`, `scripts/make_tables.py` and `scripts/make_figures.py` rebuild results, table and
   figures from `data/congelado/`; `scripts/verify_figures.py` checks everything again.

### Full path (`python run_all.py --completo`, CPU hours)

Redoes, from the anonymized panel, the five simulations of the faithful port and requires byte-for-byte equality
with the frozen outputs. On 2026-11-04, on this machine (Python 3.12.12, numpy 2.5.4, scipy 1.18.1), with the code
of this version, all five came out identical (log in `docs/rodada-completa-2026-11-04.log`):

| Module | Cells | sha256 (prefix) | Rerun = frozen |
|---|---|---|---|
| `verificacoes_port` | 4 blocks | `c9401110` | yes |
| `diagnostico_ado` | 8 | `f3061d97` | yes |
| `diagnostico_ado_mascara_real` | 3 | `d7f31226` | yes |
| `diagnostico_ado_escala` | 12 | `f3f25245` | yes |
| `diagnostico_ado_juizes` | 10 | `1f2d332e` | yes |

Bit-for-bit equality depends on the numpy and scipy versions (`requirements.lock`). With other versions, the rates
should agree within Monte Carlo error, not byte for byte.

**Why the anonymized panel reproduces the numbers.** The origin study identifies the mayor by CPF. Here, each
mayor-municipality pair has a two-digit code, assigned in the same lexicographic order as the original keys
within each municipality. As a result, `np.unique` over `"município|prefeito"` returns the same indices it returned
with the CPF, and the cells with a mayor effect draw the effects in the same order (checked on the 55,479 rows
before publishing).

### Comparison with Stata

`stata/rifle_celulas.do` runs the central cells in the official package. **It has not been tested**: the author did
not have Stata. Stata's random number generator is not numpy's, so the comparison is statistical, not bit for bit.
Two precautions the package's code imposes: the leader needs an identifier that is unique across the whole panel
(the package groups by `group(leader)` across all units) and the period needs to be the half-term number, 1 to 10
(`nostitch` recognizes stretches by `period == period[_n-1] + 1`).

## Seal 2 — frozen evidence (not redone here)

The 21 outputs in `data/congelado/` have their sha256 pinned in `code/montar_results.py`; the script stops if any of
them changes. Of these, 16 are not redone here:

- **the study's own engine** (`diagnostico_alinhamento`, `diagnostico_escala`, `diagnostico_costura`,
  `diagnostico_borda`, `simulacoes`, `simulacoes_v2`, `confirmacao_tamanho_v2`): they depend on modules of the
  origin study that read data with CPF;
- **analysis of the real data** (`resultado_v2`, `resultado_v2_corrigido`, `diagnostico_calibracao`,
  `diagnostico_heterocedasticidade`, `nota_iptu`) and the **independent reproduction** with its own engine
  (`astra_*`): they depend on the real municipal indices.

### Declared provenance gaps

1. **Four outputs of the old pilot are not in any hash chain**: `diagnostico_costura.json`,
   `diagnostico_borda.json`, `simulacoes.json` and `simulacoes_v2.json`. The modules that generated them were
   registered before running (`simulacoes.py` in the `piloto` chain seq 20, `simulacoes_v2.py` seq 29); the
   outputs were not. The 64% figure in Section 5.6 of the paper comes from `diagnostico_costura.json`. Their sha256
   has been pinned since 2026-10-31; `tests/test_cadeias_origem.py` lists the four as an exception and requires
   registration of all the others.
2. **Precedence in time declared, not authenticated.** The chains guarantee integrity and order, but the timestamps come
   from the files' modification dates. There is no external timestamp (the Zenodo record of 2026-11-07, DOI 10.5281/zenodo.24044367, is the first
   external anchor).
3. **Reading rule outside the chain.** The reading rule for the ten cells added in the revision
   (`diagnostico_ado_juizes`) was written in the paper's preregistration before running, but that file was not in
   a chain; the module entered the `piloto` chain (seq 51) before its output (seq 52).
4. **Latent defect in the real-data analysis code (not published here).** Preregistration v2 requires switching to
   the restricted version of the test if the size diagnostic fails; the controller in `analise/analise_v2.py` does
   not make that switch on its own. No effect on the result: the diagnostic passed (5.1%), and the analysis ran a
   single time, recorded. The code was not changed after running.
5. **Notes in the origin chains naming tools.** The notes of some records in
   `data/origem/analise.manifest.jsonl` and `data/origem/piloto.manifest.jsonl` name the tools and the language
   models used in the revision (the paper describes them only as three models from different families). The notes
   stay as they were recorded: editing them would break the chain.

### The sealed run

`runs/` holds one sealed run, the one of this version. Its `prev` field is the `chain_head` of the run sealed in
release v1.0.0-rc1 (the release that minted the DOI), which stays in that release. `scripts/verify_chain.py`
recomputes the current run from disk.

## What this package does not redo

- The collection and processing of the raw data (TSE, Saeb, Siconfi, SIM and Sinasc), which identify people.
- The preregistered analysis of the real indices.
- The literature search and the review of the text.
