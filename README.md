
# mkdocs-jupyterlite

A MkDocs plugin for embedding interactive notebooks in your docs via jupyterlite.

![Recording of a JupyterLite notebook embedded in MkDocs](https://raw.githubusercontent.com/NickCrews/mkdocs-jupyterlite/main/docs/assets/recording.gif)

Say you have a notebook `example.ipynb` in your awesome project, and you want
users to be able to play around with it.
By using [JupyterLite](https://jupyterlite.readthedocs.io/),
you can run Jupyter notebooks directly in the browser without any server-side dependencies.

## Examples

- [This project's documentation site](https://nickcrews.github.io/mkdocs-jupyterlite)
- [Mismo's documentation site](https://nickcrews.github.io/mismo/examples/patent_deduplication/)
  (Mismo was the initial motivation for this plugin.)

## Installation

### Step 1: Install the plugin from [PyPI](https://pypi.org/project/mkdocs-jupyterlite/):

```bash
python -m pip install mkdocs-jupyterlite
```

### Step 2: Configure your `mkdocs.yml` file

See the [mkdocs.yml](https://github.com/NickCrews/mkdocs-jupyterlite/blob/main/mkdocs.yml)
that configures [this project's site](https://nickcrews.github.io/mkdocs-jupyterlite).

```yaml
site_name: mkdocs-jupyterlite
site_url: https://nickcrews.github.io/mkdocs-jupyterlite/
repo_url: https://github.com/nickcrews/mkdocs-jupyterlite/

nav:
  - Home: index.md
  - Notebook 1: notebook.ipynb

plugins:
  - jupyterlite:
      # An easy way to turn off the entire plugin.
      enabled: true
      # Uses the same syntax as .gitignore:
      # Include and exclude files using glob patterns, the last matching pattern
      # determines if a file is included or excluded.
      notebook_patterns:
        # Include all. This is the default.
        - "**/*.ipynb"
        # Exclude drafts.
        - "!**/draft_*.ipynb"
        # Re-include a specific draft.
        - "project/drafts/draft_keep.ipynb"
        # Exclude a notebook at the root. Doesn't match /a/b/c/top_secret.ipynb
        - "!/top_secret.ipynb"
      # Add custom wheels so that when you
      # `%pip install my-package` in the notebook,
      # the micropip library has a backup after PyPI to fall back on.
      wheels:
        # Specify a url directly.
        - url: "https://files.pythonhosted.org/packages/2d/2c/7f32ba15302847f0cd0d01101470b2f427ec5b3a07756f41c823c01c0242/ibis_framework-10.5.0-py3-none-any.whl"
        # Run a shell command that dynamically
        # builds/fetches/creates 0 to N .whl files in the given {wheels_dir}
        # (which will be replaced by this plugin with a real, temporary directory).
        - command: "curl -L -o {wheels_dir}/cowsay-6.1-py3-none-any.whl https://files.pythonhosted.org/packages/f1/13/63c0a02c44024ee16f664e0b36eefeb22d54e93531630bd99e237986f534/cowsay-6.1-py3-none-any.whl"
        - command: "cd src/package_not_on_pypi/ && uv build --out-dir {wheels_dir}"
```

Here are the details on the configuration options:

### `enabled`

bool, whether or not the plugin is enabled. Defaults to `true`.

### `notebook_patterns`

A list of patterns that uses [gitignore](https://git-scm.com/docs/gitignore)
semantics to include and exclude files.
The last matching pattern will be used to determine if a file is a notebook.

These are resolved relative to your MkDocs `docs_dir` directory,
which by default for most projects is `docs/`.
So if you have a notebook at `docs/notebook.ipynb`,
that corresponds to the pattern `/notebook.ipynb`.

For all files that match, the content of the page will be an
iframe that embeds the JupyterLite Notebook html.

### `wheels`

A list of wheels to include in the JupyterLite environment.
The simplest form is to specify a file path or URL directly underneath the `url` key.

Or, if you use the `command` key, this is interpreted as a shell command.
This plugin will replace the `{wheels_dir}` placeholder with a temporary directory,
and then run the command in the directory that the `mkdocs` command was run from.
This command must place/create 0 to N `.whl` files in the given `{wheels_dir}` directory.

## Related Work and Alternatives

- [Binder](https://mybinder.org/):
  A popular tool for creating sharable, interactive environments for Jupyter notebooks.
  Requires a full docker environment and a remote server.
  The notebook is hosted separately from your docs, so a user has to click
  away in order to run the notebook.
  Takes 30-60 seconds to boot up a new environment.
- [mkdocs-jupyter](https://github.com/danielfrg/mkdocs-jupyter):
  A MkDocs plugin that embeds *static* Jupyter notebooks into your MkDocs site.
  That project is very similar to this one, except that one executes and
  renders the notebooks as static HTML at build time, so they
  aren't interactive on the site.
  It is much more mature than this project though.
- [jupyterlite-sphinx](https://github.com/jupyterlite/jupyterlite-sphinx):
  A Sphinx extension that integrates JupyterLite within your Sphinx documentation.
  That project is very similar to this one, except that it is for Sphinx
  instead of MkDocs.
  It also has more features than this project.
  I will probably use that as inspiration for future development of this project,
  for example how it uses `environment.yml` to specify python packages that will
  be included in the JupyterLite environment.
- [jupyterlite](https://github.com/jupyterlite/jupyterlite):
  The core project that powers this plugin.
  You *can* use jupyterlite directly in your docs, it just is more work.
  You would need to a build step to package your notebooks, other files, and python
  dependencies into a single static .html file.
  Then you would need to inject this .html file into the proper pages of your MkDocs site.
  This plugin automates that process for you.

## Style Compatibility with `mkdocs-material`

[mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
is a popular theme for MkDocs that is compatible with this plugin.
But, in its css, it limits the `max-width` of the content area to be 61rem.
This is just small enough that the JupyterLite notebook, when embedded,
thinks it is on a mobile device, and so many of the important UI elements of JupyterLite,
such as the "add cell below" hover menu, are hidden.
To get around this, see https://github.com/NickCrews/mkdocs-jupyterlite/blob/main/docs/extra.css

## Contributing

I want this to be usable for other people, so file an issue if you want
to use this in your site, but run into any problems.

Possible improvements:

- [x] Include custom python wheels into the JupyterLite environment.
- [x] Fix the TOC so clicking headers actually scrolls in the iframe.
- [ ] Passing an entire jupyter-lite.json config file.
- [ ] Instead of using an iframe, actually inline the contents of the generated HTML?