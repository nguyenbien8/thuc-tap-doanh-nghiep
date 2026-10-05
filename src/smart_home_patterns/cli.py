from __future__ import annotations

import argparse
import json

from .demo import write_demo
from .io import load_config, write_frame
from .pipeline import load_events, run_pipeline, run_preprocessing
from .strands_adapter import download_strands


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smart-home",
        description="Discover recurring human habits in smart-home sensor data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  smart-home generate-demo\n"
            "  smart-home run\n"
            "  smart-home download-strands\n"
            "  smart-home run --config configs/strands_aruba.yaml\n"
            "  smart-home experiments\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_config(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default=None, metavar="PATH",
                       help="config YAML (default: configs/config.yaml)")

    demo_p = sub.add_parser("generate-demo", help="write the reproducible synthetic event log")
    demo_p.add_argument("--output", default=None, help="output CSV (default: data.raw_path)")
    demo_p.add_argument("--days", type=int, default=None, help="days to simulate (default: data.demo_days)")
    add_config(demo_p)

    strands_p = sub.add_parser("download-strands", help="download the public STRANDS activity archive")
    strands_p.add_argument("--target", default="data/raw/strands", help="extraction folder")

    prep_p = sub.add_parser("preprocess", help="step 1 only: clean events and build sessions")
    prep_p.add_argument("--input", default=None, metavar="PATH", help="input CSV (overrides config)")
    add_config(prep_p)

    run_p = sub.add_parser("run", help="step 1 + step 2 + report")
    run_p.add_argument("--input", default=None, metavar="PATH", help="input CSV (overrides config)")
    add_config(run_p)

    exp_p = sub.add_parser("experiments", help="baseline comparison and sensitivity analysis")
    exp_p.add_argument("--configs", nargs="+", default=["configs/config.yaml", "configs/strands_aruba.yaml"])
    exp_p.add_argument("--output", default="reports/results/experiments")

    args = parser.parse_args()

    if args.command == "download-strands":
        print(f"STRANDS dataset extracted to {download_strands(args.target)}")
        return
    if args.command == "experiments":
        from .experiments import run_experiments  # heavy: imported only when needed
        run_experiments(args.configs, args.output)
        print(f"Experiment tables written to {args.output}")
        return

    config = load_config(args.config)
    if args.command == "generate-demo":
        output = args.output or config["data"]["raw_path"]
        write_demo(output, args.days or config["data"].get("demo_days", 28), config["data"]["random_seed"])
        print(f"Demo data written to {output}")
    elif args.command == "preprocess":
        prep = run_preprocessing(config, load_events(config, args.input))
        processed = config["output"]["processed_dir"]
        write_frame(prep.events, f"{processed}/clean_events.csv")
        write_frame(prep.sessions, f"{processed}/sessions.csv")
        print(json.dumps(prep.report, indent=2))
    elif args.command == "run":
        metrics = run_pipeline(config, args.input)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        print(f"Results written to {config['output']['results_dir']}")


if __name__ == "__main__":
    main()
