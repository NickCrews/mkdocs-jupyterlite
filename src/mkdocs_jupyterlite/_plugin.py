import fnmatch
import logging
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import markdown
import nbformat
from mkdocs.config.base import Config as BaseConfig
from mkdocs.config.config_options import Type as OptionType
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import TableOfContents, get_toc
from nbconvert import MarkdownExporter

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


class JupyterlitePluginConfig(BaseConfig):
    enabled = OptionType(bool, default=True)
    notebook_patterns = OptionType(list, default=[])


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
        notebook_paths = []
        for file in files:
            if is_notebook(
                relative_path=file.src_uri,
                notebook_patterns=self.config.notebook_patterns,
            ):
                log.info("[jupyterlite] including notebook: " + str(file.abs_src_path))
                outfiles.append(NotebookFile(file))
                notebook_paths.append(file.abs_src_path)
            else:
                log.debug("[jupyterlite] ignoring file: " + str(file.abs_src_path))
                outfiles.append(file)
        notebooks = [Path(config.docs_dir) / p for p in notebook_paths]
        _build.build_site(
            notebooks=notebooks,
            pip_urls=[],
            output_dir=Path(self._jupyterlite_build_dir.name),
        )
        return Files(outfiles)

    def on_pre_page(
        self, page: Page, /, *, config: MkDocsConfig, files: Files
    ) -> Page | None:
        if not isinstance(page.file, NotebookFile):
            return page
        log.info("[jupyterlite] on_pre_page " + str(page.file.src_uri))

        def new_render(self: Page, config: MkDocsConfig, files: Files) -> None:
            body = f"""
            <iframe src="{config.site_url}jupyterlite/notebooks/index.html?path={page.file.src_uri}"
                width="100%"
                height="800px"
                frameborder="1">
            </iframe>
            """
            self.content = body
            toc, title_in_notebook = get_nb_toc_and_title(page.file.abs_src_path)
            self.toc = toc
            if title_in_notebook:
                self.title = title_in_notebook

        # replace render with new_render for this object only
        page.render = new_render.__get__(page, Page)
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
    for pattern in notebook_patterns:
        if fnmatch.fnmatch(relative_path, pattern):
            return True
    return False


# Hooks for development
def on_startup(command: str, dirty: bool) -> None:
    log.info("[jupyterlite][development] plugin started.")


def on_page_markdown(markdown: str, page: Any, config: MkDocsConfig, files: Any) -> str:
    log.info("[jupyterlite][development] plugin started.")
    plugin = JupyterlitePlugin()
    return plugin.on_page_markdown(markdown, page=page, config=config, files=files)


def on_post_page(output: str, page: Page, config: MkDocsConfig) -> str:
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
    md = markdown.Markdown(extensions=["toc"])
    md.convert(markdown_source)
    toc = get_toc(md.toc_tokens)
    title = None
    for token in md.toc_tokens:
        if token["level"] == 1 and title is None:
            title = token["name"]
    return toc, title
