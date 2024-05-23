import argparse
from bson import ObjectId
import yaml

import argparse

from benchmarks import run_benchmark
from evaluate_benchmark import (
    evaluate_test_runs,
    evaluate_all_unevaluated_benchmarks,
    evaluate_new_benchmarks_for_model,
)
from analyze import get_scores_for_test_runs, generate_box_plot, generate_scatter_plot


def benchmark():
    print("Running benchmark...")
    run_benchmark()


def evaluate(test_run_ids):
    print(f"Evaluating test runs: {test_run_ids}")
    evaluate_test_runs(test_run_ids)


def analyze(test_run_ids):
    print(f"Analyzing test runs: {test_run_ids}")

    test_run_ids = [ObjectId(id) for id in test_run_ids]
    scores = get_scores_for_test_runs(test_run_ids)
    generate_box_plot(scores)
    generate_scatter_plot(scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Command line tool for benchmarking, evaluating, and analyzing test runs."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run the benchmark")
    benchmark_parser.set_defaults(func=benchmark)

    # Evaluate command
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate test runs")
    evaluate_parser.add_argument(
        "--test-run-ids",
        type=str,
        help="List of test run IDs to evaluate, e.g. '[1,2,3]'",
    )
    evaluate_parser.add_argument(
        "--unevaluated",
        action="store_true",
        help="Evaluate only test runs that have not been evaluated yet",
    )
    evaluate_parser.add_argument(
        "--model",
        type=str,
        help="Evaluate all test runs for a specific model, e.g. 'claude-3-opus'",
    )
    evaluate_parser.set_defaults(func=evaluate)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze test runs")
    analyze_parser.add_argument(
        "--test-run-ids",
        type=str,
        required=True,
        help="List of test run IDs to analyze, e.g. '[1,2,3]'",
    )
    analyze_parser.set_defaults(func=analyze)

    args = parser.parse_args()

    # if args.command == "evaluate" or args.command == "analyze":
    #     test_run_ids = eval(args.test_run_ids)
    #     args.func(test_run_ids)
    # else:
    #     args.func()
    if args.command == "evaluate":
        if args.unevaluated:
            evaluate_unevaluated_benchmarks()
        elif args.model:
            evaluate_new_benchmarks_for_model(args.model)
        elif args.test_run_ids:
            test_run_ids = eval(args.test_run_ids)
            args.func(test_run_ids)
    elif args.command == "analyze":
        test_run_ids = eval(args.test_run_ids)
        args.func(test_run_ids)
    else:
        args.func()


def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Load a configuration file")
