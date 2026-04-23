project = "PieThorn"
author = "Officer Erik 1K-88"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["version-switcher.js"]
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "versions.html",
    ]
}
