# Input generation

All model inputs for this study derive from one base directory,
`classI_jsons/` - one **bare** AF3-schema JSON per target: just chain IDs and
sequences, with the `unpairedMsa`/`pairedMsa`/`templates` fields entirely
absent (not set empty). Built by `af3/build_classI_jsons.py` from Lu et al.'s
per-target sequence file, `TCR-pMHC-folding-benchmark-main/benchmark_data/class-i-seqs.json`
(see the top-level README's [Setup](../README.md#setup) for obtaining that
repository).

Because those fields are *absent* rather than empty, this base JSON is what
AF3's own data pipeline consumes directly for the **MSA + template**
condition - it computes the MSA and searches for templates itself at
runtime. The other conditions are derived by explicitly disabling that
search:

```
classI_jsons/                                     (built by af3/build_classI_jsons.py)
  │
  ├─ af3/create_jsons_no_templates_classI.py       → classI_jsons_patched/        (MSA only: sets `templates: []`)
  ├─ af3/create_jsons_no_msa_no_template_classI.py → classI_jsons_no_msa/         (No MSA: sets MSA fields + `templates` empty)
  │
  ├─ intellifold2/create_yaml.py                   → classI_yamls/                (base AF3→IntelliFold YAML conversion)
  │     └─ intellifold2/add_empty_msa_to_yamls.py  → classI_yamls_no_msa/         (No MSA: sets per-chain msa: empty)
  │
  └─ protenix/make_protenix_jsons.py                → classI_jsons_protenix_*/    (base AF3→Protenix JSON schema conversion;
                                                                                    Protenix's own --use_msa/--use_template
                                                                                    flags select the condition at run time)
```

Each of these was run once per model to produce the condition-specific input
directory consumed by that model's scripts under `../model_runs/`.
