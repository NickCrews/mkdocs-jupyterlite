import importlib.metadata
import warnings

from mkdocs_jupyterlite._plugin import JupyterlitePlugin as JupyterlitePlugin
from mkdocs_jupyterlite._plugin import (
    JupyterlitePluginConfig as JupyterlitePluginConfig,
)

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"
