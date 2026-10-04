"""Check inward imports and IO ownership without importing application code."""

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "backend" / "app"
OUTER_LIBRARIES = {
    "fastapi",
    "starlette",
    "mcp",
    "anthropic",
    "lightgbm",
    "numpy",
    "sqlite3",
    "psycopg",
    "urllib",
    "requests",
    "httpx",
    "subprocess",
}
FILE_IO = {"read_text", "write_text", "read_bytes", "write_bytes", "mkdir", "open"}


def violations(source: str, layer: str) -> list[str]:
    errors = []
    allowed = {"app.domain"} if layer == "domain" else {"app.domain", "app.application"}
    for node in ast.walk(ast.parse(source)):
        modules = []
        if isinstance(node, ast.Import):
            modules = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = ["app", layer]
                base = package[:len(package) - node.level + 1]
                module = ".".join([*base, *([module] if module else [])])
            modules = [module]
            if module == "app":
                modules = [f"app.{item.name}" for item in node.names]
        for module in modules:
            if module.startswith("app.") and not any(
                module == prefix or module.startswith(prefix + ".")
                for prefix in allowed
            ):
                errors.append(f"{node.lineno}: outer import {module}")
            if module.split(".")[0] in OUTER_LIBRARIES:
                errors.append(f"{node.lineno}: IO/provider import {module}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                errors.append(f"{node.lineno}: filesystem IO")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in FILE_IO:
                errors.append(f"{node.lineno}: filesystem IO {node.func.attr}")
    return errors


def check(app_dir=APP):
    return [
        f"{path.relative_to(app_dir)}:{error}"
        for layer in ("domain", "application")
        for path in (app_dir / layer).rglob("*.py")
        for error in violations(path.read_text(), layer)
    ]


if __name__ == "__main__":
    failures = check()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Architecture boundaries passed (Pydantic contracts intentionally allowed).")
