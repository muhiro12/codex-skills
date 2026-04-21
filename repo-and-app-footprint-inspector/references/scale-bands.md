# Market Scale Bands

These bands are heuristic comparisons for mobile and client app codebases.
Use them only as rough positioning, not as an empirical industry fact.

## Meaningful Production LOC

- Count only non-empty, non-comment-only lines in source files.
- Exclude tests from the headline comparison.
- Exclude assets, localization files, and generated/build outputs from the headline LOC number.

## Heuristic Bands

| Band | Meaningful production LOC | Typical interpretation |
| --- | --- | --- |
| Tiny | 0-4,999 | Prototype or very focused utility app |
| Small | 5,000-19,999 | Small shipped app with a limited feature set |
| Medium | 20,000-59,999 | Mid-size consumer app |
| Large | 60,000-149,999 | Mature multi-surface product |
| Very Large | 150,000-299,999 | Large product suite with substantial shared code |
| Platform-Scale | 300,000+ | Platform-scale app family |

## Interpretation Notes

- A codebase with watch apps, widgets, or shared libraries can move up a band without implying a larger binary.
- Heavy asset catalogs may make the repository large while keeping the meaningful LOC band moderate.
- Some mature apps stay in a lower LOC band by aggressively sharing frameworks or outsourcing functionality to platform APIs.
