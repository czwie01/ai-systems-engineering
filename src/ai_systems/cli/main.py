"""Public command-line interface."""

import argparse
from collections.abc import Sequence

from ai_systems.experiments import EXPERIMENTS, get_experiment


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-systems",
        description="Discover reliable AI systems engineering experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered experiments")

    explain_parser = subparsers.add_parser(
        "explain", help="show metadata for a registered experiment"
    )
    explain_parser.add_argument("experiment", help="registered experiment identifier")
    return parser


def _list_experiments() -> int:
    print("ID                          MILESTONE  AREA           STATUS")
    for experiment in EXPERIMENTS:
        print(
            f"{experiment.identifier:<27} "
            f"{experiment.milestone:<10} "
            f"{experiment.area:<14} "
            f"{experiment.status}"
        )
    return 0


def _explain(identifier: str, parser: argparse.ArgumentParser) -> int:
    experiment = get_experiment(identifier)
    if experiment is None:
        parser.error(f"unknown experiment: {identifier}")

    print(f"id: {experiment.identifier}")
    print(f"name: {experiment.name}")
    print(f"milestone: {experiment.milestone}")
    print(f"area: {experiment.area}")
    print(f"status: {experiment.status}")
    print(f"engineering question: {experiment.engineering_question}")
    print(f"intended invariant: {experiment.intended_invariant}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = _parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "list":
        return _list_experiments()
    if arguments.command == "explain":
        return _explain(arguments.experiment, parser)

    parser.error(f"unknown command: {arguments.command}")


if __name__ == "__main__":
    raise SystemExit(main())
