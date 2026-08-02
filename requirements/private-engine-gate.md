# Private Career Compass engine gate

This public Pages repository does not check out or read the private `job_search`
repository. GitHub Pages therefore proves only that the public PWA and its
public snapshot can be packaged and deployed.

The engine contract is checked separately in `JUNPINMOON/job-search`, on its
`master` branch, by `tools/check_career_compass_contract.py` and
`.github/workflows/career-compass-engine.yml`. That private gate checks the
same five producer/consumer contracts that used to be referenced from this
public ledger:

- DATA-282: enriched graduate-shortlist input and source lineage
- DATA-290: private feedback-evidence overlay lineage
- DATA-291: public source labels use the official 고용24 name
- DATA-302: saved/rejected feedback identities stay out of candidates
- DATA-303: saved currentness is downgraded when evidence is stale

The two gates are intentionally independent and require no GitHub token or
cross-repository checkout. A passing Pages run is not evidence that the local
worker ran, and a passing private contract run is not evidence that Pages
deployed. Review both workflow statuses before treating a release as ready for
the iPhone.
