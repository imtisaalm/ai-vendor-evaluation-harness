import argparse
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

CRITERIA = ('accuracy', 'latency', 'cost', 'data_handling', 'integration_effort')
DEFAULT_WEIGHTS = dict(accuracy=0.35, latency=0.20, cost=0.15, data_handling=0.20, integration_effort=0.10)
SCHEMA = """CREATE TABLE IF NOT EXISTS pilots (
 id INTEGER PRIMARY KEY, vendor TEXT NOT NULL, run_at TEXT NOT NULL,
 accuracy REAL NOT NULL, latency REAL NOT NULL, cost REAL NOT NULL,
 data_handling REAL NOT NULL, integration_effort REAL NOT NULL,
 notes TEXT NOT NULL DEFAULT ''
)"""

def validate(scores, weights=DEFAULT_WEIGHTS):
    if set(scores) != set(CRITERIA):
        raise ValueError('Scores must include all five criteria')
    if set(weights) != set(CRITERIA) or any(v < 0 for v in weights.values()) or abs(sum(weights.values()) - 1) > 1e-8:
        raise ValueError('Weights must be nonnegative and sum to 1')
    if any(not isinstance(v, (int, float)) or not 0 <= v <= 5 for v in scores.values()):
        raise ValueError('Scores must be between 0 and 5')

def score(scores, weights=DEFAULT_WEIGHTS):
    validate(scores, weights)
    return round(sum(scores[k] * weights[k] for k in CRITERIA), 3)

def connect(path):
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn

def add_pilot(conn, vendor, scores, notes='', run_at=None):
    validate(scores)
    if not vendor.strip():
        raise ValueError('Vendor is required')
    timestamp = run_at or datetime.now(timezone.utc).isoformat()
    conn.execute('INSERT INTO pilots (vendor, run_at, accuracy, latency, cost, data_handling, integration_effort, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 (vendor, timestamp, *(scores[k] for k in CRITERIA), notes))
    conn.commit()

def report(conn, weights=DEFAULT_WEIGHTS):
    rows = conn.execute('SELECT vendor, COUNT(*) AS runs, AVG(accuracy), AVG(latency), AVG(cost), AVG(data_handling), AVG(integration_effort) FROM pilots GROUP BY vendor').fetchall()
    output = []
    for row in rows:
        scores = dict(zip(CRITERIA, row[2:]))
        output.append(dict(vendor=row[0], runs=row[1], weighted_score=score(scores, weights), **{k: round(v, 2) for k,v in scores.items()}))
    return sorted(output, key=lambda x: (-x['weighted_score'], x['vendor']))

def main():
    parser = argparse.ArgumentParser(description='Record and compare vendor pilots')
    parser.add_argument('--db', default='pilots.sqlite3')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('seed')
    add = sub.add_parser('add')
    add.add_argument('vendor')
    for key in CRITERIA:
        add.add_argument('--' + key.replace('_', '-'), type=float, required=True)
    add.add_argument('--notes', default='')
    show = sub.add_parser('report')
    show.add_argument('--csv', default=None)
    show.add_argument('--weights', default=None, help='JSON file mapping criteria to weights')
    args = parser.parse_args()
    with connect(args.db) as conn:
        if args.command == 'seed':
            if conn.execute('SELECT COUNT(*) FROM pilots').fetchone()[0]:
                raise SystemExit('Database already contains pilots; seed skipped')
            examples = [
                ('Northstar', [4.5, 3.8, 3.0, 4.2, 3.7]),
                ('Cedar', [4.0, 4.6, 4.2, 3.6, 4.4]),
                ('Harbor', [3.7, 4.0, 4.8, 4.5, 3.2]),
            ]
            for name, values in examples:
                add_pilot(conn, name, dict(zip(CRITERIA, values)), 'Synthetic pilot')
            print('Added three example pilots')
        elif args.command == 'add':
            add_pilot(conn, args.vendor, {k: getattr(args, k) for k in CRITERIA}, args.notes)
            print('Pilot recorded')
        else:
            weights = json.loads(Path(args.weights).read_text()) if args.weights else DEFAULT_WEIGHTS
            rows = report(conn, weights)
            print('Vendor           Runs  Weighted / 5')
            for item in rows:
                print(f"{item['vendor']:<16} {item['runs']:>4}  {item['weighted_score']:>12.3f}")
            if args.csv:
                with open(args.csv, 'w', newline='') as handle:
                    writer = csv.DictWriter(handle, fieldnames=['vendor','runs','weighted_score',*CRITERIA]); writer.writeheader(); writer.writerows(rows)

if __name__ == '__main__':
    main()
