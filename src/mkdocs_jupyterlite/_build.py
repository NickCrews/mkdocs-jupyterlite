from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Generator, Protocol
from urllib.parse import urlparse

log = logging.getLogger("mkdocs.plugins.jupyterlite")


class WheelSource(Protocol):
    command: str
    url: str


def build_site(
    *,
    docs_dir: Path,
    notebook_relative_paths: Iterable[Path],
    wheel_sources: Iterable[WheelSource],
    output_dir: Path,
) -> None:
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with _get_src_dir() as working_dir:
        log.debug(f"[jupyterlite] using working dir: {working_dir}")
        _write_jupyter_lite_json(working_dir)
        wheels_dir = working_dir / "wheels"
        wheel_urls = _get_wheel_urls(wheels_dir, wheel_sources)
        for notebook in notebook_relative_paths:
            src = docs_dir / notebook
            dst = working_dir / "files" / notebook
            dst.parent.mkdir(parents=True, exist_ok=True)
            log.debug(f"[jupyterlite] copying {src} to build {dst}")
            shutil.copy(src, dst)
        wheel_args = []
        for wheel_url in wheel_urls:
            wheel_args.extend(["--piplite-wheels", wheel_url])
        cmd = [
            "jupyter",
            "lite",
            "build",
            "--debug",
            "--contents",
            "files",
            *wheel_args,
            "--no-libarchive",
            "--apps",
            "notebooks",
            "--no-unused-shared-packages",
            "--output-dir",
            str(output_dir),
        ]
        log.info("[jupyterlite] running build command")
        _run_command(cmd, cwd=working_dir)
        assert output_dir.exists(), "Output directory was not created"

        # Inject iframe scroll handler into JupyterLite
        _inject_scroll_handler(output_dir)


def _write_jupyter_lite_json(working_dir: Path) -> None:
    data = {
        "jupyter-lite-schema-version": 0,
        "jupyter-config-data": {
            # By default, jupyterlite saves the state of the notebook to the client's
            # browser, and on reload of the page, the notebook will be restored to that state.
            # The problem is that this local state overrides the contents sent from the server.
            # So, if you edit a notebook rebuild your docs, and refresh the page,
            # you still see the old version.
            # These settings make it so that the state is never stored on the client,
            # and is refreshed from the server on every page load.
            # Not ideal: it would be great if the user's state persisted until the
            # data on the server actually *changed*, but that doesn't appear possible yet.
            # See https://github.com/jupyterlite/jupyterlite/issues/1706#issuecomment-3187140714
            "enableMemoryStorage": True,
            "settingsStorageDrivers": ["memoryStorageDriver"],
            "contentsStorageDrivers": ["memoryStorageDriver"],
        },
    }
    path = working_dir / "jupyter-lite.json"
    path.write_text(json.dumps(data, indent=4))


def _run_command(cmd: str | list[str], **kwargs):
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    log.info("[jupyterlite] running command: " + cmd_str)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            text=True,
            **kwargs,
        )
        if result.stdout:
            log.debug("[jupyterlite] command output:\n" + result.stdout)
        if result.stderr:
            log.debug("[jupyterlite] command stderr:\n" + result.stderr)
    except subprocess.CalledProcessError as e:
        log.error("[jupyterlite] command failed with error code: " + str(e.returncode))
        if e.stdout:
            log.error("[jupyterlite] command stdout:\n" + e.stdout)
        if e.stderr:
            log.error("[jupyterlite] command stderr:\n" + e.stderr)
        raise


def _get_wheel_urls(
    working_dir: Path, wheel_sources: Iterable[WheelSource]
) -> list[str]:
    """Returns a list of wheel paths for the given wheel sources."""
    wheel_urls = []
    wheels_dir = working_dir.absolute() / "wheels"
    wheels_dir.mkdir(parents=True, exist_ok=True)
    for source in wheel_sources:
        if source.url and source.command:
            raise ValueError("Wheel source cannot have both URL and command", source)
        if not source.url and not source.command:
            raise ValueError("Wheel source must have either URL or command", source)
        if source.url:
            log.info(f"[jupyterlite] including wheel URL: {source.url}")
            url = urlparse(source.url)
            if not url.scheme or url.scheme == "file":
                # Local file URL
                wheel_file = Path(url.path).name
                dst = shutil.copy(source.url, wheels_dir / wheel_file)
                wheel_urls.append(str(Path(dst).absolute()))
            else:
                wheel_urls.append(source.url)
        elif source.command:
            with tempfile.TemporaryDirectory() as tmpdir:
                actual_command = source.command.format(wheels_dir=tmpdir)
                log.info("[jupyterlite] running wheel command")
                _run_command(actual_command, shell=True)
                wheel_files = list(Path(tmpdir).glob("*.whl"))
                if not wheel_files:
                    # This is explicitly OK.
                    pass
                for wheel in wheel_files:
                    file_name = wheel.name
                    dst = shutil.copy(wheel, wheels_dir / file_name)
                    log.debug(f"[jupyterlite] including wheel URL: {file_name}")
                    wheel_urls.append(str(dst.absolute()))
    return wheel_urls


def _inject_scroll_handler(output_dir: Path) -> None:
    """Inject the scroll handler JavaScript into JupyterLite notebook index.html."""
    # Get the path to the static scroll handler file
    static_dir = Path(__file__).parent / "static"
    scroll_handler_src = static_dir / "iframe-scroll-handler.js"

    if not scroll_handler_src.exists():
        log.warning(
            f"[jupyterlite] scroll handler script not found at {scroll_handler_src}"
        )
        return

    # Copy the scroll handler to the jupyterlite build
    notebooks_dir = output_dir / "notebooks"
    if not notebooks_dir.exists():
        log.warning(f"[jupyterlite] notebooks directory not found at {notebooks_dir}")
        return

    scroll_handler_dest = notebooks_dir / "iframe-scroll-handler.js"
    shutil.copy(scroll_handler_src, scroll_handler_dest)
    log.info(f"[jupyterlite] copied scroll handler to {scroll_handler_dest}")

    # Inject script tag into notebooks/index.html
    index_html_path = notebooks_dir / "index.html"
    if not index_html_path.exists():
        log.warning(f"[jupyterlite] index.html not found at {index_html_path}")
        return

    html_content = index_html_path.read_text()

    # Check if already injected
    if "iframe-scroll-handler.js" in html_content:
        log.debug("[jupyterlite] scroll handler already injected")
        return

    # Inject the script tag before </body> using regex to handle various whitespace
    script_tag = '<script src="iframe-scroll-handler.js"></script>\n  </body>'
    html_content = re.sub(r"\s*</body>", f"\n    {script_tag}", html_content, count=1)

    index_html_path.write_text(html_content)
    log.info("[jupyterlite] injected scroll handler into notebooks/index.html")


@contextlib.contextmanager
def _get_src_dir() -> Generator[Path, None, None]:
    # For debugging, allow setting the build directory
    if (src_dir_str := os.environ.get("MKDOCS_JUPYTERLITE_SRC_DIR")) is not None:
        p = Path(src_dir_str)
        shutil.rmtree(p, ignore_errors=True)
        p.mkdir(parents=True, exist_ok=True)
        yield p
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
