
# mkdocs-jupyterlite

A MkDocs plugin for embedding interactive notebooks in your docs via jupyterlite.

![Screenshot of a JupyterLite notebook embedded in MkDocs](https://raw.githubusercontent.com/NickCrews/mkdocs-jupyterlite/main/docs/assets/screenshot.png)

Say you have a notebook `example.ipynb` in your awesome project, and you want
users to be able to play around with it.
By using [JupyterLite](https://jupyterlite.readthedocs.io/),
you can run Jupyter notebooks directly in the browser without any server-side dependencies.

See [this project's documentation site](https://nickcrews.github.io/mkdocs-jupyterlite)
for a live example.

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
      enabled: true
      notebook_patterns:
        # include all
        - "**/*.ipynb",
        # exclude drafts
        - "!**/draft_*.ipynb",  
        # re-include a specific draft
        - "project/drafts/draft_keep.ipynb",
        # exclude an anchored notebook
        - "!/top_secret.ipynb",
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

## Contributing

I want this to be usable for other people, so file an issue if you want
to use this in your site, but run into any problems.

Possible improvements:

- Include custom python wheels into the JupyterLite environment.
- Passing an entire jupyter-lite.json config file.
- Instead of using an iframe, actually inline the contents of the generated HTML?
- Fix the TOC so clicking headers actually scrolls in the iframe.