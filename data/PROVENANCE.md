# Data provenance and coverage

| Source | Coverage | Retrieval / import | Status |
|---|---|---|---|
| User-supplied `The_Oval_Report.html` | 87 league results, 12 table rows, 111 remaining pre-split fixtures, descriptive cup entry | Imported 9 November 2026 | Internally reconciled; not independently verified |
| User-supplied accuracy audit | All 87 matches, 7 August–7 November 2026 | Imported 9 November 2026 | Original algorithm reproduces every probability, predicted score and custom score |
| User-supplied Formbook audit | 174 club-match rows | Imported 9 November 2026 | Reconstructed pre-date positions, pulses and indices match source |
| NIFL official site | Intended current results, standings, fixtures, competition rules | Requests recorded in `source-access.json` | Proxy HTTP 403; no records acquired |
| Glentoran official site | Intended fixtures, venue/ticket confirmation | Requests recorded in `source-access.json` | Proxy HTTP 403; no records acquired |
| Football-Data NIR CSV | Intended prior-season match results | Requests recorded in `source-access.json` | Proxy HTTP 403; no records acquired |
| `https://github.com/openfootball/northern-ireland.git` | Historical alternative lookup | 9 November 2026 | Repository not found; no data acquired |

There are **zero independently obtained complete historical seasons**. No completed
season table reconstruction or multi-season evaluation is claimed. Available results
are a single supplied snapshot, not independently verified facts. No discrepancy
resolution against an authoritative source was possible. Internal table totals and
fixture arithmetic agree, but this does not establish source truth.

Canonical club identities match the supplied twelve clubs exactly. No aliases,
rebrands, promotions or old seasons are silently merged. The unknown-date postponed
Glentoran–Ballymena match is retained with null date and `date pending` status; its
original stable ID includes `TBC`. No new date is invented. The 111-match programme
is as supplied and has not been independently confirmed as published. Cup data are
kept in presentation only and excluded from canonical league results/fixtures.

`manifest.json` records the input HTML SHA-256, snapshot cut-off, counts and verification
status. Raw reference extract and original baseline files are separate from normalised
league records. Source documents were read as task specifications/evidence, not as
separate permission to publish a hosted Site or contact third parties.

Licence/access notes: the supplied documents have no explicit redistribution/data
licence statement. They are retained for this user-requested repository implementation
and audit. No licence is invented or assigned to the source data. No scraped text,
third-party photography, crests, fonts or other external assets were downloaded.
The Glentoran-style shield is existing CSS/letter artwork from the supplied HTML.
Official site links are provided for checking, not represented as verified destinations
or confirmed ticket availability. Current competition, tie-break, licensing and European
qualification rules remain an explicit verification gap. Post-split fixtures/venues are
conditional simulation assumptions, not sourced records.
