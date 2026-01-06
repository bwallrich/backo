# pylint: skip-file
import os
import sys
import toml

sys.path.insert(0, os.path.abspath("../../../stricto/"))
sys.path.insert(0, os.path.abspath("../../"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


project_information = toml.load("../../pyproject.toml")
print("-----------------------------------")
print(project_information["project"])
print("-----------------------------------")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = project_information["project"]["name"]
author = project_information["project"]["authors"][0]["name"]
copyright = f"2025, {author}"
release = project_information["project"]["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

extensions = ["sphinx.ext.autodoc", "myst_parser", "sphinxcontrib.mermaid"]

templates_path = ["_templates"]
exclude_patterns = []

myst_fence_as_directive = ["mermaid"]
myst_heading_anchors = 4

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
