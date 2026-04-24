from __future__ import annotations

import argparse
import html
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Iterable
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
INFO_RENDERED_SUFFIXES = {".rst", ".txt"}
SHARED_NAV_RELATIVE_PATHS = (
    Path("docs/_static/custom.css"),
    Path("docs/_static/top-nav.js"),
    Path("docs/_static/version-switcher.js"),
    Path("docs/_templates/versions.html"),
)
PROJECT_SITE_PAGES = (
    (Path("CHANGELOG.rst"), Path("changelog.html")),
)


def build_site_nav_stylesheet_href(root_prefix: str) -> str:
    return f"{root_prefix}_static/site-nav.css"


def build_site_nav_script_src(root_prefix: str) -> str:
    return f"{root_prefix}_static/top-nav.js"


def build_site_nav_placeholder_html(
    root_prefix: str,
    *,
    current_path: str,
    current_label: str | None = None,
) -> str:
    label_attr = f' data-current-label="{html.escape(current_label, quote=True)}"' if current_label else ""
    return (
        '<nav class="site-top-nav" aria-label="Site"'
        f' data-site-root-prefix="{html.escape(root_prefix, quote=True)}"'
        f' data-current-path="{html.escape(current_path, quote=True)}"{label_attr}></nav>'
    )


def build_inline_json_script(script_id: str, payload: object) -> str:
    serialized = json.dumps(payload, indent=2).replace("</", "<\\/")
    return f'<script id="{script_id}" type="application/json">\n{serialized}\n</script>'


def inject_inline_json_scripts(document: str, scripts: list[str]) -> str:
    if not scripts:
        return document

    block = "\n".join(scripts)
    if re.search(r"</body>", document, flags=re.IGNORECASE):
        return re.sub(r"</body>", block + "\n</body>", document, count=1, flags=re.IGNORECASE)
    return document + "\n" + block


def wrap_info_html_document(document: str, root_prefix: str, *, title: str = "PieThorn", current_path: str) -> str:
    safe_title = html.escape(title)
    nav_html = build_site_nav_placeholder_html(root_prefix, current_path=current_path)
    stylesheet_href = build_site_nav_stylesheet_href(root_prefix)
    stylesheet_link = f'<link rel="stylesheet" href="{stylesheet_href}">'
    script_src = build_site_nav_script_src(root_prefix)
    script_tag = f'<script src="{script_src}" defer></script>'
    wrapped = document.strip()
    lowered = wrapped.lower()

    has_html = "<html" in lowered
    has_head = "<head" in lowered
    has_body = "<body" in lowered

    if not has_html:
        new_wrapped = f"<!DOCTYPE html>\n<html lang=\"en\">\n"
        if not has_head:
            new_wrapped += (
                "<head>\n"
                "<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "</head>\n"
            )
        if has_head and has_body:
            new_wrapped += wrapped
        elif has_head:
            new_wrapped += f"{wrapped}\n<body>\n</body>"
        elif has_body:
            new_wrapped += wrapped
        else:
            new_wrapped += f"<body>\n{wrapped}\n</body>"
        new_wrapped += "\n</html>"
        wrapped = new_wrapped
        lowered = wrapped.lower()

    if "<head" not in lowered:
        wrapped = re.sub(
            r"(<html[^>]*>)",
            r"\1\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n</head>",
            wrapped,
            count=1,
            flags=re.IGNORECASE,
        )
        lowered = wrapped.lower()

    if "<body" not in lowered:
        html_close_match = re.search(r"</html>", wrapped, flags=re.IGNORECASE)
        head_close_match = re.search(r"</head>", wrapped, flags=re.IGNORECASE)
        if html_close_match and head_close_match:
            body_inner = wrapped[head_close_match.end():html_close_match.start()].strip()
            wrapped = (
                wrapped[:head_close_match.end()]
                + "\n<body>\n"
                + body_inner
                + "\n</body>\n"
                + wrapped[html_close_match.start():]
            )
        elif head_close_match:
            wrapped = wrapped[:head_close_match.end()] + "\n<body>\n</body>" + wrapped[head_close_match.end():]
        else:
            wrapped += "\n<body>\n</body>"
        lowered = wrapped.lower()

    has_nav = '<nav class="site-top-nav"' in lowered
    has_stylesheet_link = stylesheet_href in wrapped
    has_script_tag = script_src in wrapped

    if "</head>" in lowered and not has_stylesheet_link:
        wrapped = re.sub(r"</head>", stylesheet_link + "\n</head>", wrapped, count=1, flags=re.IGNORECASE)
        lowered = wrapped.lower()
    elif "</head>" not in lowered and not has_stylesheet_link:
        wrapped = stylesheet_link + "\n" + wrapped
        lowered = wrapped.lower()

    if "</body>" in lowered and not has_script_tag:
        wrapped = re.sub(r"</body>", script_tag + "\n</body>", wrapped, count=1, flags=re.IGNORECASE)
        lowered = wrapped.lower()
    elif "</body>" not in lowered and not has_script_tag:
        wrapped += "\n" + script_tag
        lowered = wrapped.lower()

    if "<title" not in lowered and "</head>" in lowered:
        wrapped = re.sub(r"</head>", f"<title>{safe_title}</title>\n</head>", wrapped, count=1, flags=re.IGNORECASE)
        lowered = wrapped.lower()

    if "<body" in lowered and not has_nav:
        if re.search(r"<body[^>]*\bclass=", wrapped, flags=re.IGNORECASE):
            wrapped = re.sub(
                r'(<body[^>]*\bclass=")([^"]*)(")',
                r'\1\2 info-page\3',
                wrapped,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            wrapped = re.sub(r"(<body)([^>]*>)", r'\1 class="info-page"\2', wrapped, count=1, flags=re.IGNORECASE)
        wrapped = re.sub(r"(<body[^>]*>)", r"\1\n" + nav_html, wrapped, count=1, flags=re.IGNORECASE)
    elif "<body" not in lowered and not has_nav:
        wrapped = nav_html + wrapped

    if "<body" in wrapped.lower() and "info-page" not in wrapped.lower():
        if re.search(r"<body[^>]*\bclass=", wrapped, flags=re.IGNORECASE):
            wrapped = re.sub(
                r'(<body[^>]*\bclass=")([^"]*)(")',
                r'\1\2 info-page\3',
                wrapped,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            wrapped = re.sub(r"(<body)([^>]*>)", r'\1 class="info-page"\2', wrapped, count=1, flags=re.IGNORECASE)

    if "<main class=\"info-page__content\">" not in wrapped.lower():
        if "<body" in wrapped.lower():
            body_match = re.search(r"<body[^>]*>", wrapped, flags=re.IGNORECASE)
            if body_match:
                body_start = body_match.end()
                body_end_match = re.search(r"</body>", wrapped, flags=re.IGNORECASE)
                body_end = body_end_match.start() if body_end_match else len(wrapped)
                body_content = wrapped[body_start:body_end]
                if nav_html in body_content:
                    remaining = body_content.replace(nav_html, "", 1).strip()
                    wrapped = (
                        wrapped[:body_start]
                        + "\n"
                        + nav_html
                        + "\n<main class=\"info-page__content\">\n"
                        + remaining
                        + "\n</main>\n"
                        + wrapped[body_end:]
                    )
        else:
            wrapped = f"{nav_html}\n<main class=\"info-page__content\">\n{wrapped}\n</main>"

    return wrapped


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def run_git_binary(repo_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def hash_version_inputs(repo_root: Path, tag: str) -> str:
    digest = hashlib.sha256()
    ls_tree_output = run_git_binary(
        repo_root,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        tag,
        "--",
        *DOC_INPUT_PATHS,
    )

    for entry in ls_tree_output.split(b"\0"):
        if not entry:
            continue
        metadata, path_bytes = entry.split(b"\t", 1)
        object_id = metadata.rsplit(b" ", 1)[-1]
        digest.update(path_bytes)
        digest.update(b"\0")
        digest.update(object_id)
        digest.update(b"\0")

    # These files are injected into historical checkouts before the build.
    for relative_path in SHARED_NAV_RELATIVE_PATHS:
        source_path = repo_root / relative_path
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_path.read_bytes())
        digest.update(b"\0")

    digest.update(INJECTED_CONF_MARKER.encode("utf-8"))
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
    archive = subprocess.Popen(
        ["git", "archive", "--format=tar", tag],
        cwd=repo_root,
        stdout=subprocess.PIPE,
    )
    assert archive.stdout is not None

    try:
        with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
            tar.extractall(destination, filter="data")
    finally:
        archive.stdout.close()

    return_code = archive.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, ["git", "archive", "--format=tar", tag])


def inject_shared_navigation(repo_root: Path, worktree: Path) -> None:
    docs_root = worktree / "docs"
    if not docs_root.exists():
        raise FileNotFoundError(f"Tag checkout at {worktree} does not contain docs/.")

    for relative_path in SHARED_NAV_RELATIVE_PATHS:
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
if "top-nav.js" not in html_js_files:
    html_js_files.append("top-nav.js")
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


def copy_shared_site_assets(repo_root: Path, output_dir: Path) -> None:
    static_dir = output_dir / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / "docs/_static/custom.css", static_dir / "site-nav.css")
    shutil.copy2(repo_root / "docs/_static/top-nav.js", static_dir / "top-nav.js")


def make_relative_symlink(target: Path, link_path: Path) -> None:
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_dir() and not link_path.is_symlink():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()

    relative_target = os.path.relpath(target, link_path.parent)
    link_path.symlink_to(relative_target, target_is_directory=True)


def iter_info_files(info_dir: Path) -> Iterable[Path]:
    for path in sorted(info_dir.rglob("*")):
        if path.is_file():
            yield path


def info_output_relative_path(info_dir: Path, source_path: Path) -> Path:
    relative_path = source_path.relative_to(info_dir)
    if source_path.suffix.lower() in INFO_RENDERED_SUFFIXES:
        return relative_path.with_suffix(".html")
    return relative_path


def root_prefix_for_output(output_relative_path: Path) -> str:
    parent = output_relative_path.parent
    if str(parent) == ".":
        return ""
    return "../" * len(parent.parts)


def render_rst_info_page(source_path: Path, destination: Path, root_prefix: str, current_path: str) -> None:
    from docutils.core import publish_parts

    source = source_path.read_text(encoding="utf-8")
    parts = publish_parts(source=source, writer_name="html5")
    title = parts.get("title", source_path.stem)
    body_html = parts.get("body") or parts.get("whole") or ""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        wrap_info_html_document(
            body_html,
            root_prefix,
            title=title,
            current_path=current_path,
        ),
        encoding="utf-8",
    )


def render_plain_text_info_page(source_path: Path, destination: Path, root_prefix: str, current_path: str) -> None:
    text = html.escape(source_path.read_text(encoding="utf-8"))
    title = source_path.stem
    body_html = f"<pre>{text}</pre>"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        wrap_info_html_document(
            body_html,
            root_prefix,
            title=title,
            current_path=current_path,
        ),
        encoding="utf-8",
    )


def inject_nav_into_html(source_path: Path, destination: Path, root_prefix: str, current_path: str) -> None:
    document = source_path.read_text(encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        wrap_info_html_document(
            document,
            root_prefix,
            title=source_path.stem,
            current_path=current_path,
        ),
        encoding="utf-8",
    )


def copy_info_site(repo_root: Path, output_dir: Path) -> bool:
    info_dir = repo_root / "info"
    if not info_dir.exists():
        return False

    if not info_dir.is_dir():
        raise NotADirectoryError(f"{info_dir} exists but is not a directory.")

    reserved_paths = {"docs"}
    seen_outputs: dict[Path, Path] = {}

    for source_path in iter_info_files(info_dir):
        relative_path = source_path.relative_to(info_dir)
        if relative_path.parts and relative_path.parts[0] in reserved_paths:
            raise ValueError(
                f"info/{relative_path.as_posix()} conflicts with a reserved Pages path; "
                "place documentation-independent site files outside info/docs."
            )

        output_relative_path = info_output_relative_path(info_dir, source_path)
        previous_source = seen_outputs.get(output_relative_path)
        if previous_source is not None:
            raise ValueError(
                "Multiple info/ files map to the same output path: "
                f"{previous_source.relative_to(info_dir).as_posix()} and "
                f"{relative_path.as_posix()} -> {output_relative_path.as_posix()}"
            )
        seen_outputs[output_relative_path] = source_path

    for output_relative_path, source_path in seen_outputs.items():
        destination = output_dir / output_relative_path
        root_prefix = root_prefix_for_output(output_relative_path)
        current_path = output_relative_path.as_posix()
        suffix = source_path.suffix.lower()
        if suffix == ".rst":
            render_rst_info_page(source_path, destination, root_prefix, current_path)
        elif suffix == ".txt":
            render_plain_text_info_page(source_path, destination, root_prefix, current_path)
        elif suffix == ".html":
            inject_nav_into_html(source_path, destination, root_prefix, current_path)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)

    return True


def render_project_site_pages(repo_root: Path, output_dir: Path) -> None:
    for source_relative_path, output_relative_path in PROJECT_SITE_PAGES:
        source_path = repo_root / source_relative_path
        if not source_path.exists():
            continue

        destination = output_dir / output_relative_path
        if destination.exists() or destination.is_symlink():
            raise ValueError(
                f"Project site page output conflict: {output_relative_path.as_posix()} "
                f"already exists before rendering {source_relative_path.as_posix()}."
            )

        root_prefix = root_prefix_for_output(output_relative_path)
        current_path = output_relative_path.as_posix()
        suffix = source_path.suffix.lower()
        if suffix == ".rst":
            render_rst_info_page(source_path, destination, root_prefix, current_path)
        elif suffix == ".txt":
            render_plain_text_info_page(source_path, destination, root_prefix, current_path)
        elif suffix == ".html":
            inject_nav_into_html(source_path, destination, root_prefix, current_path)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)


def label_from_output_path(output_path: Path) -> str:
    if output_path == Path("index.html"):
        return "Home"

    if output_path.name == "index.html" and output_path.parent != Path("."):
        source = output_path.parent.name
    else:
        source = output_path.stem

    return source.replace("-", " ").replace("_", " ").title()


def extract_html_title(html_path: Path) -> str | None:
    content = html_path.read_text(encoding="utf-8")
    match = re.search(r"<title>(.*?)</title>", content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(1)).strip() or None


def collect_site_nav_pages(output_dir: Path) -> list[dict[str, str]]:
    pages: list[dict[str, str]] = []

    for html_path in sorted(output_dir.rglob("*.html")):
        relative_path = html_path.relative_to(output_dir)
        if not relative_path.parts:
            continue
        if relative_path.parts[0] in {"docs", "_static"}:
            continue

        label = label_from_output_path(relative_path)
        if relative_path != Path("index.html"):
            label = extract_html_title(html_path) or label
        pages.append({"label": label, "path": relative_path.as_posix()})

    pages.sort(key=lambda page: (page["path"] != "index.html", page["path"].count("/"), page["path"]))
    return pages


def write_site_nav_manifest(output_dir: Path, latest: str) -> dict[str, object]:
    payload = {
        "pages": collect_site_nav_pages(output_dir),
        "docs": {
            "home": "docs/",
            "latest": "docs/latest/index.html",
            "latest_version": latest,
        },
    }
    (output_dir / "site-nav.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_homepage(output_dir: Path, latest: str) -> None:
    nav_html = build_site_nav_placeholder_html("", current_path="index.html")
    stylesheet_href = build_site_nav_stylesheet_href("")
    script_src = build_site_nav_script_src("")
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PieThorn</title>
    <link rel="stylesheet" href="{stylesheet_href}">
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
    {nav_html}
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
    <script src="{script_src}" defer></script>
  </body>
</html>
"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")


def write_docs_site_files(docs_dir: Path, versions: list[str], digests: dict[str, str]) -> dict[str, object]:
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
    return payload


def embed_runtime_data(output_dir: Path, site_nav_payload: dict[str, object], versions_payload: dict[str, object]) -> None:
    site_nav_script = build_inline_json_script("site-nav-data", site_nav_payload)
    versions_script = build_inline_json_script("versions-data", versions_payload)

    for html_path in sorted(output_dir.rglob("*.html")):
        relative_path = html_path.relative_to(output_dir)
        if not relative_path.parts or relative_path.parts[0] == "_static":
            continue

        scripts = [site_nav_script]
        if relative_path.parts[0] == "docs" and relative_path.name.endswith(".html"):
            scripts.append(versions_script)

        content = html_path.read_text(encoding="utf-8")
        if 'id="site-nav-data"' in content:
            scripts = [script for script in scripts if 'id="site-nav-data"' not in script]
        if 'id="versions-data"' in content:
            scripts = [script for script in scripts if 'id="versions-data"' not in script]
        if not scripts:
            continue

        html_path.write_text(inject_inline_json_scripts(content, scripts), encoding="utf-8")


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
    copy_shared_site_assets(repo_root, output_dir)

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
            digest = hash_version_inputs(repo_root, version)
            digests_by_version[version] = digest

            if digest not in canonical_builds:
                extract_tag(repo_root, version, worktree_path)
                inject_shared_navigation(repo_root, worktree_path)
                canonical_path = build_root / digest
                build_docs(worktree_path, canonical_path)
                canonical_builds[digest] = canonical_path

            make_relative_symlink(canonical_builds[digest], docs_dir / version)

    if not copy_info_site(repo_root, output_dir):
        write_homepage(output_dir, versions[-1])
    render_project_site_pages(repo_root, output_dir)
    site_nav_payload = write_site_nav_manifest(output_dir, versions[-1])
    versions_payload = write_docs_site_files(docs_dir, versions, digests_by_version)
    embed_runtime_data(output_dir, site_nav_payload, versions_payload)


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
