import contextlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Generator

log = logging.getLogger("mkdocs.plugins.jupyterlite")


def build_site(
    *,
    docs_dir: Path,
    notebook_relative_paths: Iterable[Path],
    pip_urls: Iterable[str],
    output_dir: Path,
) -> None:
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with get_src_dir() as working_dir:
        log.debug(f"[jupyterlite] using working dir: {working_dir}")
        write_jupyter_lite_config(
            out_path=working_dir / "jupyter_lite_config.json",
            pip_urls=pip_urls,
        )
        for notebook in notebook_relative_paths:
            src = docs_dir / notebook
            dst = working_dir / "files" / notebook
            dst.parent.mkdir(parents=True, exist_ok=True)
            log.debug(f"[jupyterlite] copying {src} to build {dst}")
            shutil.copy(src, dst)
        cmd = [
            "jupyter",
            "lite",
            "build",
            "--debug",
            "--contents",
            "files",
            "--no-libarchive",
            "--apps",
            "notebooks",
            "--no-unused-shared-packages",
            "--output-dir",
            str(output_dir),
        ]
        log.info("[jupyterlite] running build command: " + " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=working_dir,
                check=True,
            )
            if result.stdout:
                log.debug("[jupyterlite] build output:\n" + result.stdout)
            if result.stderr:
                log.debug("[jupyterlite] build stderr:\n" + result.stderr)
        except subprocess.CalledProcessError as e:
            log.error("[jupyterlite] build failed")
            if e.stdout:
                log.error("[jupyterlite] build stdout:\n" + e.stdout)
            if e.stderr:
                log.error("[jupyterlite] build stderr:\n" + e.stderr)
            raise
        assert output_dir.exists(), "Output directory was not created"


def write_jupyter_lite_config(
    *,
    out_path: Path,
    pip_urls: Iterable[str],
) -> None:
    config = {
        "JupyterLiteAddon": {
            "piplite_urls": list(pip_urls),
        }
    }
    out_path.write_text(json.dumps(config, indent=2))


@contextlib.contextmanager
def get_src_dir() -> Generator[Path, None, None]:
    # For debugging, allow setting the build directory
    if (src_dir_str := os.environ.get("MKDOCS_JUPYTERLITE_SRC_DIR")) is not None:
        p = Path(src_dir_str)
        shutil.rmtree(p, ignore_errors=True)
        p.mkdir(parents=True, exist_ok=True)
        yield p
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
