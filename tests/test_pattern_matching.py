from mkdocs_jupyterlite._plugin import is_notebook


def test_notebook_patterns():
    def check(path: str, patterns: list[str]) -> bool:
        # This redirection allows us to pass as positional args
        return is_notebook(relative_path=path, notebook_patterns=patterns)

    patterns = [
        "**/*.ipynb",  # include all
        "!**/draft_*.ipynb",  # drop drafts
        "/project/drafts/draft_keep.ipynb",  # re-include a specific draft
        "!/top_secret.ipynb",  # exclude anchored
    ]
    assert check("a/draft_temp.ipynb", patterns) is False
    assert check("project/drafts/draft_keep.ipynb", patterns) is True
    assert check("x/top_secret.ipynb", patterns) is True
    assert check("top_secret.ipynb", patterns) is False
