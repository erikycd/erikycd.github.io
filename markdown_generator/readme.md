# Jupyter notebook markdown generator

These .ipynb files are Jupyter notebook files that convert a TSV containing structured data about talks (`talks.tsv`) or presentations (`presentations.tsv`) into individual markdown files that will be properly formatted for the academicpages template. The notebooks contain a lot of documentation about the process. The .py files are pure python that do the same things if they are executed in a terminal, they just don't have pretty documentation.


## Google Scholar top publications scraper

Use `google_scholar_featured_publications.py` to fetch the most-cited publications from your Google Scholar profile and regenerate `/_data/featured_publications.yml` (used by `/publications/`).

Example:

```bash
python3 markdown_generator/google_scholar_featured_publications.py \
  --scholar-url "https://scholar.google.es/citations?user=7Bf-zB8AAAAJ&hl=es" \
  --top 5
```

Monthly execution example (cron):

```bash
0 3 1 * * cd /path/to/erikycd.github.io && python3 markdown_generator/google_scholar_featured_publications.py --scholar-url "https://scholar.google.es/citations?user=7Bf-zB8AAAAJ&hl=es" --top 5
```

