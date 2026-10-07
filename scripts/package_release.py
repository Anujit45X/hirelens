"""Build a source-only upload archive: python -m scripts.package_release."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def release_files():
    """Explicit allowlist keeps data, logs, environments and secrets out of the release."""
    paths = [ROOT / name for name in (
        "app.py", "README.md", "DEPLOYMENT.md", "requirements.txt",
        "requirements-lock.txt", "pytest.ini", ".gitignore", ".streamlit/config.toml",
        ".github/workflows/tests.yml",
    )]
    for directory in ("hirelens", "scripts", "tests"):
        paths.extend((ROOT / directory).glob("*.py"))
    return sorted(paths)


def main():
    destination = ROOT / "dist" / "hirelens-source.zip"
    destination.parent.mkdir(exist_ok=True)
    paths = release_files()
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Packaged {len(paths)} source files: {destination}")


if __name__ == "__main__":
    main()
