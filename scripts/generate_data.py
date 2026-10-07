"""Run from the project root: python -m scripts.generate_data."""
import argparse
from pathlib import Path

from hirelens.config import DATABASE_PATH, SEED
from hirelens.database import write_database
from hirelens.generate import generate_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HireLens acquisition cohorts.")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    args = parser.parse_args()
    frame = generate_data(args.seed)
    write_database(frame, args.database)
    csv_path = args.database.with_suffix(".csv")
    frame.to_csv(csv_path, index=False)
    print(f"Synthetic data: {len(frame):,} rows; seed={args.seed}")
    print(f"SQLite: {args.database.resolve()}")
    print(f"CSV: {csv_path.resolve()}")


if __name__ == "__main__":
    main()
