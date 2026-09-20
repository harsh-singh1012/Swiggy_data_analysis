"""
Executes every .sql file in this folder against swiggy.db and saves each
statement's result as a CSV under sql/results/, plus prints a preview.
This proves the SQL actually runs against real data rather than being
illustrative-only.
"""
import sqlite3
import pandas as pd
import glob
import os

os.makedirs("results", exist_ok=True)
conn = sqlite3.connect("swiggy.db")

sql_files = sorted(glob.glob("0[1-4]_*.sql"))

for path in sql_files:
    base = os.path.splitext(os.path.basename(path))[0]
    raw_lines = open(path).read().splitlines()

    # Walk line by line: track the most recent non-blank comment as a running
    # label, strip comment-only lines out of the executable SQL, and split
    # into statements on ';' that appear in actual SQL (comments already removed).
    label = None
    sql_lines = []
    pending_label = None
    code_started_for_stmt = False
    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            text = stripped.lstrip("-").strip()
            if text and not text.startswith("="):
                pending_label = text
            continue
        if stripped == "":
            sql_lines.append("")
            continue
        if not code_started_for_stmt:
            label = pending_label
            code_started_for_stmt = True
        sql_lines.append(line)
        if stripped.endswith(";"):
            code_started_for_stmt = False

    full_sql = "\n".join(sql_lines)
    raw_statements = [s.strip() for s in full_sql.split(";") if s.strip()]

    # re-derive labels by re-scanning (simpler second pass, statement-aligned)
    labels = []
    cur_label = None
    buff = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            text = stripped.lstrip("-").strip()
            if text and not text.startswith("="):
                cur_label = text
            continue
        buff.append(line)
        if stripped.endswith(";"):
            labels.append(cur_label)
            buff = []

    for i, query in enumerate(raw_statements, start=1):
        lbl = labels[i-1] if i-1 < len(labels) else base
        try:
            df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"[{base} #{i}] ERROR: {e}\nQUERY WAS:\n{query}\n")
            continue
        out_name = f"results/{base}_{i:02d}.csv"
        df.to_csv(out_name, index=False)
        print(f"\n=== {base} query #{i}: {lbl} ===")
        print(f"-> {len(df)} rows saved to {out_name}")
        print(df.head(8).to_string(index=False))

conn.close()
