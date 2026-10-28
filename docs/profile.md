# Profile artwork and data

This is a GitHub profile README, rendered with Markdown, supported HTML, and local SVG images. The artwork uses vector paths and system fonts, with no JavaScript, embedded HTML, external image services, or runtime dependencies.

## Design

The exploded circuit illustration connects three interests shown in the featured repositories: interfaces, retrieval, and protocols. Its moving packets are decorative; they do not represent measured traffic, service health, or performance. The palette adapts to light and dark mode. Separate mobile images keep the text legible on smaller screens. Animation respects reduced-motion preferences.

Project descriptions were checked against the public READMEs for [FinTrace](https://github.com/KnightFang36/FinTrace), [VidMind](https://github.com/KnightFang36/VidMind), and [Stratum](https://github.com/KnightFang36/Stratum). FinTrace is described as a rule-and-graph investigation workspace using synthetic data. VidMind is marked as in development. The profile makes no claims about employers, production deployments, user counts, or benchmark results.

Visual previews use GitHub's Markdown API output with an approximation of GitHub's page styling. These are local previews, not screenshots of a published profile:

- [Desktop, dark](previews/desktop-dark.png) · [Desktop, light](previews/desktop-light.png)
- [Mobile, dark](previews/mobile-dark.png) · [Mobile, light](previews/mobile-light.png)

## Repository signal

The checked-in [snapshot](../data/profile.json) records public GitHub REST API responses reduced to repository names, links, primary languages, language byte counts, and push timestamps. It contains no credentials or private repository data.

- **Scope:** original, public, non-archived, enabled repositories with nonzero repository size. Forks and `KnightFang36/KnightFang36` are excluded. The repository list is paginated.
- **Language share:** aggregate bytes from each included repository's `/languages` endpoint. The largest four languages are shown individually; the remainder are combined as Other. This describes code composition, not time spent or proficiency. Generated or vendored code may affect GitHub's language measurements.
- **Recent pushes:** the three most recent `pushed_at` timestamps across included repositories. A push is not a deployment and does not establish who authored an individual commit.
- **Date:** the UTC date when the complete snapshot was fetched, printed on the panel. It is a dated snapshot rather than a live service indicator.
- **Failure:** all API requests and validation finish before the snapshot or artwork is written. A fetch failure makes the workflow fail and keeps the previous checked-in assets visible with their original date.

## Rebuild

Python 3.10 or later is sufficient. No packages need to be installed.

```bash
# Rebuild from the checked-in data; no network needed.
python3 scripts/build_profile.py

# Fetch fresh public data and rebuild.
python3 scripts/build_profile.py --refresh

# Check data boundaries, SVG output, and reproducibility.
python3 -m unittest discover -s tests -v
python3 scripts/build_profile.py --check
```

An optional `GH_TOKEN` or `GITHUB_TOKEN` increases the API rate limit. Authentication is not needed for these public endpoints. Never put a token in this repository.

The [workflow](../.github/workflows/profile.yml) validates pull requests and refreshes the snapshot on `main`, on manual runs, and daily at 04:23 UTC. It uses the built-in `GITHUB_TOKEN`; no personal access token is required. Only the refresh job has `contents: write`. It commits `data/profile.json` and `assets/` when they change. GitHub may delay scheduled runs, disable schedules in inactive repositories, or reject writes when branch protection requires pull requests. In those cases the dated assets continue to display; check the Actions tab and run the workflow manually or regenerate locally.

To make a manual design change, edit `scripts/build_profile.py`, rebuild, and include the generated SVGs in the same commit. Edit the README directly for project descriptions and contact links.

## Research references

The design is original. These sources informed the implementation and the focus on real work:

- [GitHub: managing your profile README](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)
- [GitHub: using your profile to enhance your resume](https://docs.github.com/en/account-and-profile/tutorials/using-your-github-profile-to-enhance-your-resume)
- [Awesome GitHub Profile READMEs](https://github.com/abhisheknaiidu/awesome-github-profile-readme), for the range of visual and automated profiles.
- [Simon Willison's self-updating profile](https://github.com/simonw/simonw), for the useful pattern of keeping real project activity in the repository itself.
- [GitHub REST: repository endpoints](https://docs.github.com/en/rest/repos/repos), for the public repository and language data.
