from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo import write_demo
from .io import load_config, read_events, write_frame
from .pipeline import run_pipeline
from .preprocessing import preprocess
from .discovery import discover_patterns, save_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover recurring activities in smart-home sensor data")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("generate-demo", help="Generate reproducible demo sensor events")
    demo.add_argument("--output", default="data/raw/smart_home_events.csv")
    demo.add_argument("--days", type=int, default=21)
    prep = sub.add_parser("preprocess", help="Clean events and build session features")
    prep.add_argument("--input", default=None)
    full = sub.add_parser("run", help="Run preprocessing and unsupervised discovery")
    full.add_argument("--input", default=None)
    args = parser.parse_args()
    config = load_config()
    if args.command == "generate-demo":
        write_demo(args.output, args.days, config["data"]["random_seed"])
        print(f"Demo data written to {args.output}")
        return
    input_path = args.input or config["data"]["raw_path"]
    if args.command == "preprocess":
        result = preprocess(
            read_events(input_path),
            config["data"]["inactivity_gap_minutes"],
            config["preprocessing"]["max_missing_fraction"],
            config["preprocessing"]["required_columns"],
        )
        write_frame(result.events, config["data"]["events_path"])
        write_frame(result.sessions, config["data"]["processed_path"])
        print(f"Preprocessed {len(result.events)} events into {len(result.sessions)} sessions")
    elif args.command == "run":
        metrics = run_pipeline(config, input_path)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
