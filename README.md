# sddyates.github.io

Personal academic website of Simon Daley-Yates, built with Jekyll on the
[Strata](https://html5up.net/strata) template by HTML5 UP.

## Updating the site

| To change…                         | Edit                                  |
|------------------------------------|---------------------------------------|
| Name, position, department, links  | `_config.yml` (`author:` block)       |
| Navigation buttons                 | `_config.yml` (`nav:`)                |
| "About Me" text and home page      | `index.html`                          |
| "Selected Work" image cards        | `_data/highlights.yml` + `images/`    |
| Research descriptions              | `research.html`                       |
| CV                                 | replace `documents/Simon_Daley_Yates_CV.pdf` |
| Header / footer on every page      | `_layouts/default.html`               |

**Publications are automatic.** `scripts/update_publications.py` queries NASA
ADS (by ORCID and author name) and writes `_data/publications.json`. The
GitHub Actions workflow in `.github/workflows/pages.yml` runs it before every
build, on every push to `master` and every Monday, so new papers and citation
counts appear without any edits. To run it locally:

```sh
ADS_TOKEN=your-token python3 scripts/update_publications.py
```

The committed `_data/publications.json` is used as a fallback if ADS can't be
reached during a build.

## One-time GitHub setup

1. **Settings → Pages → Build and deployment → Source:** GitHub Actions.
2. **Settings → Secrets and variables → Actions:** repository secret `ADS_TOKEN`
   (from https://ui.adsabs.harvard.edu/user/settings/token).

## Local preview

```sh
gem install jekyll
jekyll serve      # then open http://localhost:4000
```
