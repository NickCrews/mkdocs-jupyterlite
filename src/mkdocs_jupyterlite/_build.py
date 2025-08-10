import json
import logging
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path

log = logging.getLogger("mkdocs.plugins.jupyterlite")


def build_site(
    *,
    notebooks: Iterable[Path],
    pip_urls: Iterable[str],
    output_dir: Path,
) -> None:
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as working_dir_str:
        working_dir = Path(working_dir_str)
        write_jupyter_lite_config(
            out_path=working_dir / "jupyter_lite_config.json",
            pip_urls=pip_urls,
        )
        contents_args = []
        for notebook in notebooks:
            contents_args.extend(["--contents", str(notebook)])
        cmd = [
            "jupyter",
            "lite",
            "build",
            # *(["--debug"] if debug else []),
            "--debug",
            *contents_args,
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
                # capture_output=True,
                text=True,
                cwd=working_dir,
                check=True,
            )
            if result.stdout:
                log.debug("[jupyterlite] build output:\n" + result.stdout)
        except subprocess.CalledProcessError as e:
            log.error("[jupyterlite] build failed")
            if e.stdout:
                log.debug("[jupyterlite] build stdout:\n" + e.stdout)
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
