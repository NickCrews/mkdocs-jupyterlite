import subprocess
from pathlib import Path


def _fixture_dir() -> Path:
    return Path(__file__).parent


def test_mkdocs_build_succeeds_when_no_notebooks(tmp_path: Path) -> None:
    fixture_root = _fixture_dir()
    site_dir = tmp_path / "site"
    mkdocs_config = fixture_root / "mkdocs.yml"

    subprocess.run(
        [
            "mkdocs",
            "build",
            "--strict",
            "--config-file",
            str(mkdocs_config),
            "--site-dir",
            str(site_dir),
        ],
        check=True,
        cwd=fixture_root,
    )

    assert (site_dir / "index.html").exists()
    assert not (site_dir / "jupyterlite").exists()
