"""
KAS API Source of Truth Generator
==================================
Parses 'API Funktionen.html' and writes readme_KAS_API_SOURCE_OF_TRUTH.md.

Usage:
    python scripts/generate_source_of_truth.py
    python scripts/generate_source_of_truth.py --html "path/to/API Funktionen.html"
    python scripts/generate_source_of_truth.py --output custom_output.md
"""

import argparse
import os
import re
from bs4 import BeautifulSoup

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HTML = os.path.join(REPO_ROOT, "API Funktionen.html")
OUTPUT_FILE = os.path.join(REPO_ROOT, "readme_KAS_API_SOURCE_OF_TRUTH.md")

# Auth params are handled by the SDK client — omit them from the output so
# the Source of Truth reflects what SDK users actually need to pass.
AUTH_PARAMS = {"kas_login", "kas_auth_data", "kas_auth_type"}


def parse_html(html_path: str) -> list:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Structure: one outer div.package-indent contains 21 inner alternating pairs
    # of <ul.breadcrumb> (package name) + <div.package-indent> (package functions).
    # breadcrumbs[0] = "API Funktionen" (page header, skip).
    # breadcrumbs[k] names the package whose functions live in pkg_divs[k], k >= 1.
    breadcrumbs = soup.find_all("ul", class_="breadcrumb")
    pkg_divs = soup.find_all("div", class_="package-indent")

    results = []

    for bc, pkg_div in zip(breadcrumbs[1:], pkg_divs[1:]):
        active_item = bc.select_one("li.active a")
        if not active_item:
            continue

        pkg_name = active_item.get_text(strip=True)

        functions = []

        for anchor in pkg_div.find_all("a", id=re.compile(r"^function_")):
            func_name = anchor["id"].replace("function_", "")

            # The function div is the immediate next sibling element
            func_div = anchor.find_next_sibling("div")
            if not func_div:
                continue

            # --- Deprecated check ---
            deprecated_note = None
            first_table = func_div.find("table", class_="table-bordered")
            if first_table:
                dep_th = first_table.find("th", string=re.compile(r"deprecated", re.I))
                if dep_th:
                    td = dep_th.find_next_sibling("td")
                    deprecated_note = td.get_text(strip=True) if td else "deprecated"

            # --- Parameters ---
            req_params = []
            opt_params = []

            arg_div = func_div.find("div", class_="subelement argument")
            if arg_div:
                param_ul = arg_div.find("ul")
                if param_ul:
                    for li in param_ul.find_all("li", recursive=False):
                        name_tag = li.find("b")
                        if not name_tag:
                            continue

                        param_name = name_tag.get_text(strip=True)

                        if param_name in AUTH_PARAMS:
                            continue  # SDK handles auth internally

                        full_text = li.get_text(" ", strip=True)
                        is_optional = bool(
                            re.search(r"\boptional\b", full_text, re.I)
                            or re.search(r"\bdefault\b", full_text, re.I)
                        )

                        if is_optional:
                            default_match = re.search(
                                r"default\s*=?\s*([^)<,]+)", full_text, re.I
                            )
                            if default_match:
                                default_val = default_match.group(1).strip().rstrip(")")
                                opt_params.append(f"{param_name} [Def: {default_val}]")
                            else:
                                opt_params.append(param_name)
                        else:
                            req_params.append(param_name)

            # --- Exceptions ---
            # The exceptions table is always the LAST table in the detail block.
            exceptions = []
            detail_div = func_div.find("div", class_="detail-description")
            if detail_div:
                tables = detail_div.find_all("table", class_="table-bordered")
                if tables:
                    for th in tables[-1].find_all("th"):
                        code_tag = th.find("code")
                        if code_tag:
                            text = code_tag.get_text(strip=True)
                            if text.startswith("\\"):
                                exceptions.append(text)

            exceptions = sorted(set(exceptions))

            functions.append({
                "name": func_name,
                "req": req_params,
                "opt": opt_params,
                "exc": exceptions,
                "deprecated": deprecated_note,
            })

        if functions:
            results.append({"pkg": pkg_name, "funcs": functions})

    return results


def generate_markdown(results: list) -> str:
    lines = [
        "# KAS API — Source of Truth",
        "",
        "> Auto-generated from `API Funktionen.html`.",
        "> Auth params (`kas_login`, `kas_auth_data`, `kas_auth_type`) are omitted — the SDK handles these automatically.",
        "",
    ]

    for pkg in results:
        lines.append(f"## Package: {pkg['pkg']}")
        lines.append("")

        for func in pkg["funcs"]:
            dep = (
                f" *(deprecated: {func['deprecated']})*"
                if func.get("deprecated")
                else ""
            )
            lines.append(f"### `{func['name']}`{dep}")

            req_str = ", ".join(func["req"]) if func["req"] else "None"
            opt_str = ", ".join(func["opt"]) if func["opt"] else "None"
            exc_str = ", ".join(func["exc"]) if func["exc"] else "None"

            lines.append(f"* **Req**: {req_str}")
            lines.append(f"* **Opt**: {opt_str}")
            lines.append(f"* **Exc**: {exc_str}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate KAS API Source of Truth from HTML docs."
    )
    parser.add_argument(
        "--html",
        default=DEFAULT_HTML,
        help=f"Path to API Funktionen.html (default: repo root)",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help=f"Output markdown file (default: readme_KAS_API_SOURCE_OF_TRUTH.md)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.html):
        print(f"ERROR: HTML file not found: {args.html}")
        return 1

    print(f"Parsing:  {args.html}")
    results = parse_html(args.html)

    total_funcs = sum(len(p["funcs"]) for p in results)
    print(f"Found:    {len(results)} packages, {total_funcs} functions")
    for pkg in results:
        print(f"  {pkg['pkg']:30s}  {len(pkg['funcs'])} functions")

    md = generate_markdown(results)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Written:  {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
