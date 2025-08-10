# mkdocs-jupyterlite

A MkDocs plugin that enables embedding interactive jupyterlite notebooks in your docs.

Say you have a notebook `example.ipynb` in your awesome project, and you want
users to be able to play around with it.
In the past, you could use a tool like [Binder](https://mybinder.org/) to achieve this.
But, that requires a full docker environment and a remote server.
By using [JupyterLite](https://jupyterlite.readthedocs.io/),
you can run Jupyter notebooks directly in the browser without any server-side dependencies.

However, to use jupyterlite, you have to manually install jupyterlite and
then run a build step to package your notebooks, other files, and python
dependencies into a single static site.

This plugin automates that process for you.

## Installation

### Step 1: Install the `mkdocs-jupyterlite` package

```bash
pip install mkdocs-jupyterlite
```

### Step 2: Configure your `mkdocs.yml` file

```yaml
plugins:
  - search
  - mkdocstrings
  - etc
  - jupyterlite:
      enabled: true
      notebook_patterns:
        - "**/*.ipynb"
      pip_urls:
        - "https://pypi.org/simple"
```