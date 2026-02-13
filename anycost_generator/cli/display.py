"""Rich output helpers for the interactive CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner():
    """Print the generator banner."""
    console.print(Panel(
        "[bold]AnyCost Adaptor Generator[/bold]\n"
        "Generate customized CloudZero AnyCost Stream adaptors",
        title="anycost-generator",
        border_style="blue",
    ))


def print_class_info(adaptor_class: str, description: str):
    """Print adaptor class detection result."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan")
    table.add_column()
    table.add_row("Detected class:", adaptor_class)
    table.add_row("Description:", description)
    console.print(table)


def print_config_summary(config_dict: dict):
    """Print a summary table of the config about to be generated."""
    table = Table(title="Configuration Summary", border_style="blue")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    provider = config_dict.get("provider", {})
    api = config_dict.get("api", {})
    auth = config_dict.get("auth", {})

    table.add_row("Provider", provider.get("display_name", ""))
    table.add_row("Provider ID", provider.get("name", ""))
    table.add_row("Service Type", provider.get("service_type", ""))
    table.add_row("API Base URL", api.get("base_url", ""))
    table.add_row("Auth Method", api.get("auth_method", ""))
    table.add_row("Required Env Vars", ", ".join(auth.get("required_env_vars", [])))
    table.add_row("Class", config_dict.get("adaptor_class", "auto-detect"))

    console.print(table)


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]{message}[/bold green]")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]{message}[/bold red]")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]{message}[/bold yellow]")
