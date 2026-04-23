from __future__ import annotations

import argparse
import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


DOC_INPUT_PATHS = (
    "docs",
    "piethorn",
    "pythorn",
    "README.rst",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
)

INJECTED_CONF_MARKER = "# Injected by scripts/build_versioned_docs.py"


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    if not path.exists():
        return []

    return sorted(file_path for file_path in path.rglob("*") if file_path.is_file())


def hash_inputs(worktree: Path) -> str:
    digest = hashlib.sha256()

    for relative_path in DOC_INPUT_PATHS:
        source_path = worktree / relative_path
        for file_path in iter_files(source_path):
            digest.update(file_path.relative_to(worktree).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_path.read_bytes())
            digest.update(b"\0")

    return digest.hexdigest()[:16]


def build_docs(worktree: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(worktree) + os.pathsep + env.get("PYTHONPATH", "")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "html",
            str(worktree / "docs"),
            str(output_dir),
        ],
        check=True,
        env=env,
    )


def extract_tag(repo_root: Path, tag: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", "--format=tar", tag],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout

    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")


def inject_shared_navigation(repo_root: Path, worktree: Path) -> None:
    docs_root = worktree / "docs"
    if not docs_root.exists():
        raise FileNotFoundError(f"Tag checkout at {worktree} does not contain docs/.")

    for relative_path in (
        Path("docs/_static/custom.css"),
        Path("docs/_static/version-switcher.js"),
        Path("docs/_templates/versions.html"),
    ):
        source = repo_root / relative_path
        destination = worktree / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    conf_path = docs_root / "conf.py"
    conf_text = conf_path.read_text(encoding="utf-8")
    if INJECTED_CONF_MARKER in conf_text:
        return

    conf_text += f"""

{INJECTED_CONF_MARKER}
templates_path = list(globals().get("templates_path", []))
if "_templates" not in templates_path:
    templates_path.append("_templates")

html_static_path = list(globals().get("html_static_path", []))
if "_static" not in html_static_path:
    html_static_path.append("_static")

html_css_files = list(globals().get("html_css_files", []))
if "custom.css" not in html_css_files:
    html_css_files.append("custom.css")

html_js_files = list(globals().get("html_js_files", []))
if "version-switcher.js" not in html_js_files:
    html_js_files.append("version-switcher.js")

_default_sidebars = ["about.html", "navigation.html", "relations.html", "searchbox.html", "versions.html"]
_existing_sidebars = dict(globals().get("html_sidebars", {{}}))
if not _existing_sidebars:
    _existing_sidebars["**"] = _default_sidebars
else:
    for _pattern, _templates in list(_existing_sidebars.items()):
        _merged = list(_templates)
        if "versions.html" not in _merged:
            _merged.append("versions.html")
        _existing_sidebars[_pattern] = _merged

html_sidebars = _existing_sidebars
"""
    conf_path.write_text(conf_text, encoding="utf-8")


def make_relative_symlink(target: Path, link_path: Path) -> None:
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_dir() and not link_path.is_symlink():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()

    relative_target = os.path.relpath(target, link_path.parent)
    link_path.symlink_to(relative_target, target_is_directory=True)


def write_homepage(output_dir: Path, latest: str) -> None:
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PieThorn</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f5efe5;
        --surface: #fffaf2;
        --ink: #23180f;
        --muted: #6a5645;
        --accent: #9c3d10;
        --accent-2: #d97b2d;
        --border: #dbc6b2;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        background:
          radial-gradient(circle at top left, rgba(217, 123, 45, 0.18), transparent 32rem),
          linear-gradient(180deg, #f9f2e7 0%, var(--bg) 100%);
        color: var(--ink);
      }}

      main {{
        max-width: 64rem;
        margin: 0 auto;
        padding: 4rem 1.5rem 5rem;
      }}

      .hero {{
        display: grid;
        gap: 1.5rem;
        margin-bottom: 3rem;
      }}

      .eyebrow {{
        margin: 0;
        color: var(--accent);
        font-size: 0.9rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}

      h1 {{
        margin: 0;
        font-size: clamp(2.6rem, 8vw, 5rem);
        line-height: 0.95;
      }}

      .lede {{
        margin: 0;
        max-width: 42rem;
        color: var(--muted);
        font-size: 1.15rem;
        line-height: 1.6;
      }}

      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.9rem;
      }}

      .button {{
        display: inline-block;
        padding: 0.85rem 1.15rem;
        border: 1px solid var(--accent);
        border-radius: 999px;
        text-decoration: none;
        color: white;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        font-weight: 700;
      }}

      .button.secondary {{
        color: var(--ink);
        background: transparent;
        border-color: var(--border);
      }}

      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
        gap: 1rem;
      }}

      .card {{
        padding: 1.25rem;
        border: 1px solid var(--border);
        border-radius: 1rem;
        background: rgba(255, 250, 242, 0.92);
        box-shadow: 0 0.8rem 2rem rgba(35, 24, 15, 0.05);
      }}

      .card h2 {{
        margin-top: 0;
        margin-bottom: 0.55rem;
        font-size: 1.1rem;
      }}

      .card p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }}

      code {{
        font-family: "SFMono-Regular", Consolas, monospace;
        font-size: 0.95em;
      }}

      @media (max-width: 40rem) {{
        main {{
          padding-top: 3rem;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">GitHub Pages Home</p>
        <h1>PieThorn</h1>
        <p class="lede">
          This is the project homepage for the GitHub Pages site. Versioned documentation
          now lives under <code>/docs/</code> so the site root can host other project pages.
        </p>
        <div class="actions">
          <a class="button" href="./docs/{latest}/index.html">Open Latest Docs</a>
          <a class="button secondary" href="./docs/">Docs Home</a>
        </div>
      </section>

      <section class="grid" aria-label="Site sections">
        <article class="card">
          <h2>Documentation</h2>
          <p>Browse release-specific documentation at <code>/docs/&lt;version&gt;/</code> or use the latest alias at <code>/docs/latest/</code>.</p>
        </article>
        <article class="card">
          <h2>Version Clarity</h2>
          <p>The active documentation version is visible directly in the URL instead of being hidden at the site root.</p>
        </article>
        <article class="card">
          <h2>Future Pages</h2>
          <p>This root homepage can now be expanded with project landing content, downloads, examples, or other non-documentation pages.</p>
        </article>
      </section>
    </main>
  </body>
</html>
"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")


def write_docs_site_files(docs_dir: Path, versions: list[str], digests: dict[str, str]) -> None:
    latest = versions[-1]
    payload = {
        "latest": latest,
        "versions": [{"name": version, "path": f"{version}/"} for version in reversed(versions)],
        "builds": {version: digests[version] for version in versions},
    }
    (docs_dir / "versions.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=./latest/index.html">
    <title>PieThorn Documentation</title>
  </head>
  <body>
    <p>Redirecting to the latest documentation version, <a href="./latest/index.html">{latest}</a>.</p>
  </body>
</html>
"""
    (docs_dir / "index.html").write_text(index_html, encoding="utf-8")
    make_relative_symlink(docs_dir / versions[-1], docs_dir / "latest")


def collect_tags(repo_root: Path) -> list[str]:
    tags = run_git(repo_root, "tag", "--sort=version:refname", "--list", "v*").splitlines()
    return [tag for tag in tags if tag]


def build_versioned_site(repo_root: Path, output_dir: Path) -> None:
    versions = collect_tags(repo_root)
    if not versions:
        raise SystemExit("No tags matching 'v*' were found.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    docs_dir = output_dir / "docs"
    docs_dir.mkdir()

    build_root = docs_dir / "_builds"
    build_root.mkdir()

    digests_by_version: dict[str, str] = {}
    canonical_builds: dict[str, Path] = {}

    with tempfile.TemporaryDirectory(prefix="piethorn-docs-") as temp_dir:
        temp_root = Path(temp_dir)
        worktree_root = temp_root / "worktrees"
        worktree_root.mkdir()

        for version in versions:
            safe_name = version.replace("/", "_")
            worktree_path = worktree_root / safe_name
            extract_tag(repo_root, version, worktree_path)
            inject_shared_navigation(repo_root, worktree_path)

            digest = hash_inputs(worktree_path)
            digests_by_version[version] = digest

            if digest not in canonical_builds:
                canonical_path = build_root / digest
                build_docs(worktree_path, canonical_path)
                canonical_builds[digest] = canonical_path

            make_relative_symlink(canonical_builds[digest], docs_dir / version)

    write_homepage(output_dir, versions[-1])
    write_docs_site_files(docs_dir, versions, digests_by_version)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build versioned Sphinx docs from Git tags.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing the Git metadata.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where the assembled static site should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_versioned_site(args.repo_root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
