"""CLI entry point for the AnyCost Adaptor Generator.

Subcommands:
  generate     Generate an adaptor from a YAML config file
  validate     Validate a config file without generating
  interactive  Walk through prompts to build a config and generate
"""

from __future__ import annotations

import argparse
import sys

from anycost_generator import __version__


def cmd_generate(args):
    """Generate an adaptor from a YAML config."""
    from anycost_generator.config.loader import load_from_yaml
    from anycost_generator.engine.generator import AdaptorGenerator
    from anycost_generator.validation.config_validator import validate_config
    from anycost_generator.validation.output_validator import validate_output

    # Load and validate config
    try:
        config = load_from_yaml(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Run semantic validation
    issues = validate_config(config)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    for w in warnings:
        print(f"Warning: {w}")

    if errors:
        for e in errors:
            print(f"Error: {e}")
        sys.exit(1)

    # Generate
    generator = AdaptorGenerator(config)
    output_path = generator.generate(args.output)

    # Post-generation validation
    post_issues = validate_output(
        output_path,
        config.provider.name,
        config.auth.required_env_vars,
    )
    post_errors = [i for i in post_issues if i.severity == "error"]
    post_warnings = [i for i in post_issues if i.severity == "warning"]

    for w in post_warnings:
        print(f"Post-gen warning: {w}")

    if post_errors:
        print("\nPost-generation validation found issues:")
        for e in post_errors:
            print(f"  {e}")
        sys.exit(1)

    print("\nAll validation checks passed.")


def cmd_validate(args):
    """Validate a config file without generating."""
    from anycost_generator.config.loader import load_from_yaml
    from anycost_generator.validation.config_validator import validate_config

    try:
        config = load_from_yaml(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    print(f"Config loaded successfully: {config.provider.display_name}")
    print(f"  Class: {config.adaptor_class.value}")
    print(f"  Auth method: {config.api.auth_method.value}")
    print(f"  Required env vars: {', '.join(config.auth.required_env_vars)}")

    issues = validate_config(config)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print("\nConfig is valid.")


def cmd_interactive(args):
    """Run the interactive CLI to build a config and generate."""
    try:
        from anycost_generator.cli.interactive import run_interactive
    except ImportError as e:
        print(f"Interactive mode requires additional dependencies: {e}")
        print("Install with: pip install 'anycost-generator[dev]'")
        sys.exit(1)

    run_interactive(output_dir=args.output, save_config=args.save_config)


def main():
    parser = argparse.ArgumentParser(
        prog="anycost-generator",
        description="AnyCost Adaptor Generator - generate customized CloudZero AnyCost Stream adaptors",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate an adaptor from a YAML config")
    gen_parser.add_argument("--config", "-c", required=True, help="Path to YAML config file")
    gen_parser.add_argument("--output", "-o", required=True, help="Output directory")
    gen_parser.set_defaults(func=cmd_generate)

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate a config file without generating")
    val_parser.add_argument("--config", "-c", required=True, help="Path to YAML config file")
    val_parser.set_defaults(func=cmd_validate)

    # interactive
    int_parser = subparsers.add_parser("interactive", help="Interactive config builder and generator")
    int_parser.add_argument("--output", "-o", default="./output", help="Output directory (default: ./output)")
    int_parser.add_argument("--save-config", "-s", help="Also save the generated YAML config to this path")
    int_parser.set_defaults(func=cmd_interactive)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
