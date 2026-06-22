# Releasing pas.plugins.ldap

This package is released to [PyPI](https://pypi.org/project/pas.plugins.ldap/)
**by tagging** — the version is derived from the git tag via
[hatch-vcs](https://github.com/ofek/hatch-vcs), and publishing happens through
GitHub Actions using PyPI [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no API tokens).

There is **no** version number to bump in `pyproject.toml`. The tag *is* the
version.

## Workflows

`.github/workflows/release.yaml` defines three jobs:

| Job | Trigger | Target |
| --- | --- | --- |
| `build-package` | CI passed on `main`, a published Release, or manual dispatch | builds & inspects the sdist + wheel |
| `release-test-pypi` | after CI passes on `main` (or manual dispatch on `main`) | **Test** PyPI (in-dev builds) |
| `release-pypi` | a GitHub **Release** is *published* | **PyPI** (the real release) |

The build runs the `hatch_build.py` hook, so the compiled `.mo` translation
catalogs are always included in the artifacts.

## One-time setup (maintainers / org admins)

This only needs to be done once per project.

1. **GitHub environments** — create two environments in the repo
   (*Settings → Environments*):
   - `release-pypi`
   - `release-test-pypi`

   **Protecting `release-pypi` is required, not optional.** This repository
   lives in the `collective` org, which grants write access liberally — so
   *anyone with repo write access could otherwise publish a GitHub Release and
   push to PyPI*. With Trusted Publishing the upload runs under the workflow's
   identity in the environment, so the environment's protection rules are the
   real gate on who can release. On the `release-pypi` environment set:
   - **Required reviewers** → the actual package maintainers (e.g.
     `jensens`, `rnixx`). A PyPI upload then waits for one of them to approve
     the deployment, even if someone else published the Release.
   - **Deployment branches and tags** → restrict to the release tags (e.g. a
     tag rule like `*`) and/or `main`, so the workflow can only publish from
     intended refs.

   `release-test-pypi` can stay unprotected — in-dev builds to Test PyPI are
   low-risk.

2. **PyPI trusted publisher** — on <https://pypi.org/manage/project/pas.plugins.ldap/settings/publishing/>
   add a GitHub publisher:
   - Owner: `collective`
   - Repository: `pas.plugins.ldap`
   - Workflow name: `release.yaml`
   - Environment: `release-pypi`

3. **Test PyPI trusted publisher** — repeat on
   <https://test.pypi.org/> with environment `release-test-pypi`.

   > For a brand-new project name you may need to create the project first via
   > a "pending publisher" entry on (Test) PyPI.

## Versioning / tags

`hatch-vcs` derives the version from the latest tag:

- A commit **on** tag `X.Y.Z` builds as exactly `X.Y.Z`.
- Commits **after** a tag build as a `.devN` version based on that tag.

Because the last released tag is `1.8.4`, untagged builds are currently
versioned `1.8.4.devN`. To get **2.0.0-series** in-dev builds on Test PyPI,
push an early pre-release tag, e.g.:

```shell
git tag 2.0.0a1
git push origin 2.0.0a1
```

Use [PEP 440](https://peps.python.org/pep-0440/) pre-release tags
(`2.0.0a1`, `2.0.0b1`, `2.0.0rc1`) for alphas/betas/release candidates.

## Cutting a release

1. Make sure `main` is green and `CHANGES.rst` lists everything under the
   target version heading. Rename the `2.0.0 (unreleased)` heading to the
   release date, e.g. `2.0.0 (2026-06-22)`, and commit/merge that to `main`.
2. Create and push the tag:
   ```shell
   git checkout main && git pull
   git tag 2.0.0
   git push origin 2.0.0
   ```
3. Create a **GitHub Release** for that tag (*Releases → Draft a new
   release → choose tag `2.0.0` → Publish release*). Publishing the Release
   triggers `release-pypi`, which builds and uploads to PyPI via Trusted
   Publishing.
4. Verify the new version appears on
   <https://pypi.org/project/pas.plugins.ldap/> and that the Actions run is
   green.

## Pre-release checklist

- [ ] `CHANGES.rst` is up to date and the heading carries the release date.
- [ ] CI is green on `main` (QA + the full Plone 6.0–6.2 / Python 3.10–3.14 matrix).
- [ ] Trusted publishers and GitHub environments are configured (one-time),
      and `release-pypi` has **required reviewers** set (mandatory for this
      collective repo).
- [ ] Tag follows PEP 440 (`2.0.0`, `2.0.1`, `2.1.0a1`, …).
