# Questions to resolve

Updated: 2026-10-25. Confirmed choices are in PLAN.md; do not ask them again.

## Before production data preparation

1. **Which refreshed n1/n5 files and publications are authoritative?** Provide
   matching cleaned JSON, reference libraries, and identity-v3 composite
   libraries. Rebuilding stays in RouteInspector.
2. **Which composite vocabulary?** All eligible n1 tactics, or only tactic
   identities shared by n1 and n5? The shared option uses n5 route information
   for vocabulary selection. This is separate from the already accepted n1+n5
   single-step training exposure.
3. **Which n1 composite occurrences should be excluded?** Recommended minimum:
   remove routes sharing an n5 target under the stereo-free input identity and
   audit exact duplicate routes/reactions/motif inputs. Patent-disjointness is a
   stricter optional analysis, not yet an agreed requirement. Do not apply
   these exclusions to the deliberately n1+n5 single-step training corpus.
4. **Use all internal n1 motif targets?** Recommended yes. For `T -> A -> B -> C`,
   a composite covering `A -> B -> C` is trained on A, not on T. Root-only
   training would omit the intermediate contexts encountered during search.
5. **Which stock scope?** Proposed primary: union of cleaned n1+n5 leaves,
   identical for both arms. Per-set n5 leaf stock can be a sensitivity analysis.
   The exporter supplies all three choices without selecting one silently.

## Before training and hybrid planning

6. **Validation policy and seed budget?** The current SynPlanner CLI puts
   repeated products in training and stratifies remaining examples by rule.
   Grouped route/patent validation and seed
   control require a wrapper or an upstream interface change. Recommend using
   n1 development data for composite tuning and never n5 composite labels.
7. **Top-50 split and primary cost endpoint?** Initial proposal 40/10; ablations
   45/5 and 25/25. Choose neural evaluations and/or end-to-end time, with solve
   rate reported alongside either.
8. **Non-stock components exposed by unwrapping?** Proposed first version:
   invalidate that candidate. A later completion-search variant should charge
   every extra neural call and chemistry operation.
9. **Composite repertoire versus step compression?** Should primary composites
   require all constituent elementary rules to exist in the single-step
   vocabulary, or should this be a reported subset/ablation?
10. **Runtime resources?** Training accelerator, memory, target-level compute
    budgets, and number of model/search seeds determine final configuration.

## Already settled

Separate project and environment; no preset models; single-step training on
n1+n5; MHN with QueryCGR-rule graphs and GPS molecule encoding; leaf-derived
stock; ignore stereo; linear consecutive tactics first; library rebuilding in
RouteInspector; hybrid implementation on a new SynPlanner branch.
