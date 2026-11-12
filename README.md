# AI vendor evaluation harness

A small Python and SQLite tool for scoring AI vendors and keeping a record of pilots. You score each vendor on five criteria, and the tool keeps the scores in a database and ranks vendors on a weighted total. The three example vendors are made up.

## How to run

Python 3.10 or later. No third-party packages.

```bash
python vendor_eval.py --db pilots.sqlite3 seed
python vendor_eval.py --db pilots.sqlite3 report --csv comparison.csv
python -m unittest discover -s tests -v
```

To record a real pilot:

```bash
python vendor_eval.py add "Vendor X" --accuracy 4 --latency 3 --cost 4 --data-handling 5 --integration-effort 2 --notes "20 test requests"
```

Use `--db pilots.sqlite3` before `add` to write to the same database. You can pass `--weights weights.json` to report to use different weights. The JSON file must list all five criteria and the weights must add up to 1.

## Scoring

Each criterion is scored 0 to 5. Higher is always better. Latency means latency performance, so a faster vendor scores higher. Cost means cost efficiency. Integration effort means ease of integration.

Default weights: accuracy 35%, latency 20%, cost 15%, data handling 20%, integration effort 10%.

The report averages each vendor's pilot scores by criterion and then works out a weighted score out of 5. Each pilot run counts equally, not each test request. The seeded report ranks Cedar first at 4.110 out of 5. Those scores are illustrative, not measured.

## What it does not do

The tool only records scores a person assigns. It does not benchmark response quality on its own or check a vendor's privacy controls. A real evaluation would use a fixed test set, record actual latency and cost, check data retention and security requirements, and reject any vendor that fails a mandatory control no matter how it scores. Results are not adjusted for different sample sizes across pilots.
