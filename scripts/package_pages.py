from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (ROOT / "_site").resolve()
PUBLIC_FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "sw.js",
    "supabase-config.js",
    "manifest.webmanifest",
)
PUBLIC_DIRECTORIES = ("assets", "icons")


def main() -> None:
    if OUTPUT.parent != ROOT:
        raise RuntimeError("public artifact escaped the repository root")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for relative in PUBLIC_FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(relative)
        shutil.copy2(source, OUTPUT / relative)
    for relative in PUBLIC_DIRECTORIES:
        source = ROOT / relative
        if source.is_dir():
            shutil.copytree(source, OUTPUT / relative)
    data_output = OUTPUT / "data"
    data_output.mkdir()
    shutil.copy2(ROOT / "data" / "app-data.json", data_output / "app-data.json")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    forbidden = ("service_role", "secret_key", "refresh_token")
    for path in OUTPUT.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(token in text for token in forbidden):
            raise RuntimeError(f"forbidden secret marker in {path.relative_to(OUTPUT)}")
    file_count = sum(path.is_file() for path in OUTPUT.rglob("*"))
    print(f"Pages artifact ready: {file_count} allowlisted files in {OUTPUT}")


if __name__ == "__main__":
    main()
