import logging
from pathlib import Path
from typing import Any

from mkdocs.config.base import Config as BaseConfig
from mkdocs.config.config_options import Type as OptionType
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

log = logging.getLogger("mkdocs.plugins.jupyterlite")


class JupyterlitePluginConfig(BaseConfig):
    enabled = OptionType(bool, default=True)


class JupyterlitePlugin(BasePlugin[JupyterlitePluginConfig]):
    replacements: dict[str, list[str]] = {}

    def __init__(self):
        super().__init__()
        if isinstance(self.config, dict):
            plugin_config = JupyterlitePluginConfig()
            plugin_config.load_dict(self.config)
            self.config = plugin_config

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        if not self.config.enabled:
            return config
        return config

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Any
    ) -> str:
        return markdown

    def on_post_page(self, output: str, /, *, page: Page, config: MkDocsConfig) -> str:
        if not self.config.enabled:
            return output

        if page.abs_url is None:
            return output

        log.info("[jupyterlite] on_post_page " + str(page.abs_url))
        return output


class VirtualFile(File):
    def __init__(
        self,
        path: str,
        src_dir: str,
        dest_dir: str,
        use_directory_urls: bool,
        content: str,
    ):
        super().__init__(path, src_dir, dest_dir, use_directory_urls)
        self._content = content

    def read_text(self) -> str:
        return str(self._content)

    @property
    def abs_src_path(self) -> str:
        # Return a fake path that doesn't exist on disk
        assert self.src_dir is not None
        return str(Path(self.src_dir) / "virtual" / self.src_path)

    def copy_file(self, dirty: bool = False) -> None:
        # Don't copy the file, as it doesn't exist on disk
        pass


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
