import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl
from data.loader import load_data
from data.processor import add_performance_column
from utils.calculations import calculate_rates


def main():
    df = load_data()
    df = add_performance_column(df)

    print("Columns:", df.columns)
    has_pf = "pass_fail" in df.columns
    print("Has pass_fail:", has_pf)

    if has_pf:
        print("\npass_fail raw sample:")
        print(df.select(pl.col("pass_fail").cast(pl.Utf8, strict=False)).head(10).to_dict(as_series=False))
        print("\npass_fail normalized value_counts:")
        pf_counts = (
            df.select(
                pl.col("pass_fail")
                .cast(pl.Utf8, strict=False)
                .str.to_lowercase()
                .str.strip_chars()
                .alias("pass_fail_norm")
            )
            .to_series()
            .value_counts()
        )
        print({str(k): int(v) for k, v in zip(pf_counts["pass_fail_norm"], pf_counts["counts"])})

    print("\nperformance value_counts:")
    perf_counts = (
        df.group_by(pl.col("performance").cast(pl.Utf8, strict=False).alias("performance"))
        .agg(pl.count().alias("cnt"))
        .sort("cnt", descending=True)
    )
    print({str(row[0]): int(row[1]) for row in perf_counts.iter_rows()})

    # Result columns
    for c in [
        "theory_result",
        "practical_result",
        "theory_internal_result",
        "practical_internal_result",
        "course_result",
    ]:
        if c in df.columns:
            print(f"\n{c} value_counts:")
            s = (
                df.group_by(pl.col(c).cast(pl.Utf8, strict=False).alias(c))
                .agg(pl.count().alias("cnt"))
                .sort("cnt", descending=True)
            )
            print({str(row[0]): int(row[1]) for row in s.iter_rows()})

    print("\nComputed rates (pass, distinction, fail, unique_students, total_exams):")
    print(calculate_rates(df))


if __name__ == "__main__":
    main()

