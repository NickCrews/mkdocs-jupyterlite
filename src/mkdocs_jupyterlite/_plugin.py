from __future__ import annotations

import json
import logging
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import gitmatch
import markdown
import nbformat
from mkdocs.config.base import Config as BaseConfig
from mkdocs.config.config_options import ListOfItems, SubConfig
from mkdocs.config.config_options import Type as OptionType
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import TableOfContents, _TocToken, get_toc
from nbconvert.exporters import MarkdownExporter

from mkdocs_jupyterlite import _build

log = logging.getLogger("mkdocs.plugins.jupyterlite")


class NotebookFile(File):
    """
    Wraps a regular File object to make .ipynb files appear as valid documentation files.
    """

    def __init__(self, file: File) -> None:
        self._file = file

    def __getattr__(self, name: str) -> Any:
        return self._file.__getattribute__(name)

    def is_documentation_page(self) -> Literal[True]:
        return True


class _WheelConfig(BaseConfig):
    command = OptionType(str, default="")
    url = OptionType(str, default="")


class JupyterlitePluginConfig(BaseConfig):
    enabled = OptionType(bool, default=True)
    notebook_patterns = OptionType(list, default=["**/*.ipynb"])
    wheels = ListOfItems(SubConfig(_WheelConfig), default=[])


class JupyterlitePlugin(BasePlugin[JupyterlitePluginConfig]):
    def __init__(self):
        super().__init__()
        if isinstance(self.config, dict):
            plugin_config = JupyterlitePluginConfig()
            plugin_config.load_dict(self.config)
            self.config = plugin_config
        self._jupyterlite_build_dir = tempfile.TemporaryDirectory()

    def _cleanup(self) -> None:
        log.info(
            "[jupyterlite] cleaning up temporary build directory: "
            + str(self._jupyterlite_build_dir.name)
        )
        self._jupyterlite_build_dir.cleanup()

    def on_files(self, files: Files, config: MkDocsConfig) -> Files:
        outfiles = []
        # paths to notebooks relative to config.docs_dir
        notebook_relative_paths = []
        log.info("[jupyterlite] looking for notebook files in " + str(config.docs_dir))
        for file in files:
            if is_notebook(
                relative_path=file.src_uri,
                notebook_patterns=self.config.notebook_patterns,
            ):
                log.info("[jupyterlite] including notebook: " + str(file.src_uri))
                outfiles.append(NotebookFile(file))
                notebook_relative_paths.append(file.src_uri)
            else:
                log.debug("[jupyterlite] ignoring file: " + str(file.src_uri))
                outfiles.append(file)

        # Add the TOC handler JavaScript to the site files
        static_dir = Path(__file__).parent / "static"
        toc_handler_path = static_dir / "toc-handler.js"
        if toc_handler_path.exists():
            toc_handler_file = File(
                path="toc-handler.js",
                src_dir=str(static_dir),
                dest_dir=config.site_dir,
                use_directory_urls=False,
            )
            outfiles.append(toc_handler_file)
            log.info("[jupyterlite] added toc-handler.js to site files")

        _build.build_site(
            docs_dir=Path(config.docs_dir),
            notebook_relative_paths=notebook_relative_paths,
            wheel_sources=self.config.wheels,
            output_dir=Path(self._jupyterlite_build_dir.name),
        )
        return Files(outfiles)

    def on_pre_page(
        self, page: Page, /, *, config: MkDocsConfig, files: Files
    ) -> Page | None:
        if not isinstance(page.file, NotebookFile):
            return page

        # Calculate relative path to jupyterlite from this page
        # With use_directory_urls, each page gets its own directory (e.g., /notebook/)
        # So we need one more "../" than the number of slashes in src_uri
        page_depth = page.file.src_uri.count("/") + 1
        jupyterlite_path = "../" * page_depth + "jupyterlite"
        iframe_src = f"{jupyterlite_path}/notebooks/index.html?path={page.file.src_uri}"

        def new_render(self: Page, config: MkDocsConfig, files: Files) -> None:
            log.debug("[jupyterlite] rendering " + page.file.abs_src_path)
            log.debug("[jupyterlite] creating iframe with src " + iframe_src)

            # Calculate the relative path to the toc-handler.js from this page
            # Use the same page_depth calculation as for iframe_src
            toc_handler_path = "../" * page_depth + "toc-handler.js"

            body = f"""
            <iframe src="{iframe_src}"
                width="100%"
                height="800px"
                frameborder="1"
                id="jupyterlite-iframe">
            </iframe>
            <script src="{toc_handler_path}"></script>
            """
            self.content = body
            toc, title_in_notebook = get_nb_toc_and_title(page.file.abs_src_path)
            log.debug("[jupyterlite] TOC: " + str(toc))
            log.debug("[jupyterlite] title in notebook: " + str(title_in_notebook))
            log.debug("[jupyterlite] page title: " + str(self.title))
            self.toc = toc
            if title_in_notebook and not self.title:
                self.meta["title"] = title_in_notebook

        # replace render with new_render for this object only
        page.render = new_render.__get__(page, Page)  # ty:ignore[invalid-assignment]
        return page

    def on_post_build(self, config: MkDocsConfig) -> None:
        shutil.copytree(
            self._jupyterlite_build_dir.name,
            Path(config.site_dir) / "jupyterlite",
            dirs_exist_ok=True,
        )
        self._cleanup()

    def on_build_error(self, *, error: Exception) -> None:
        self._cleanup()


def is_notebook(*, relative_path: str | Path, notebook_patterns: Iterable[str]) -> bool:
    gi = gitmatch.compile(notebook_patterns, ignorecase=False)
    return bool(gi.match(Path(relative_path).as_posix()))


# Hooks for development
def on_startup(command: str, dirty: bool) -> None:
    log.info("[jupyterlite][development] plugin started.")


def on_page_markdown(
    markdown: str, page: Any, config: MkDocsConfig, files: Any
) -> str | None:
    log.info("[jupyterlite][development] plugin started.")
    plugin = JupyterlitePlugin()
    return plugin.on_page_markdown(markdown, page=page, config=config, files=files)


def on_post_page(output: str, page: Page, config: MkDocsConfig) -> str | None:
    log.info("[jupyterlite][development] plugin started.")
    plugin = JupyterlitePlugin()
    return plugin.on_post_page(output, page=page, config=config)


def on_files(files: Files, config: MkDocsConfig) -> Files:
    log.info("[jupyterlite][development] plugin started.")
    plugin = JupyterlitePlugin()
    return plugin.on_files(files, config)


def get_nb_toc_and_title(path: str | Path) -> tuple[TableOfContents, str | None]:
    """Returns a TOC and title (the first heading, if present) for the Notebook."""
    notebook = nbformat.reads(Path(path).read_text(), as_version=4)
    (markdown_source, _resources) = MarkdownExporter().from_notebook_node(notebook)
    log.debug("[jupyterlite] converted notebook to markdown:\n" + markdown_source)
    md = markdown.Markdown(
        # enable all extensions to improve probability that parsing works.
        extensions=[
            "admonition",
            "codehilite",
            "extra",
            "fenced_code",
            "meta",
            "sane_lists",
            "smarty",
            "toc",
            "wikilinks",
        ]
    )
    md.convert(markdown_source)
    toc_tokens: list[_TocToken] = md.toc_tokens  # type: ignore[attr-defined]
    log.debug("[jupyterlite] extracted TOC tokens: " + json.dumps(toc_tokens, indent=2))
    toc = get_toc(toc_tokens)
    title = None
    for token in toc_tokens:
        if token["level"] == 1 and title is None:
            title = token["name"]
    return toc, title
