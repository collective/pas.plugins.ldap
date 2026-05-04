# Information about the Makefile

How to use the uv, mxdev, cookiecutter-zope-instance and make based install.

## Usage

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

On the commandline, execute the ``make`` command.
Without any options, make will run nothing, so pass in a command.

Run the Zope-Server:

```bash
make run
```

Run all tests:

```bash
make test
```

All options are printed with

```bash
make help
```

``make run`` resolves dependencies in order like: *prepare*, *install*, *instance*, *run*.

The Makefile is built to detect changes.
At the first ``make run`` all steps are executed.
Subsequent calls are only starting the application server in the *run* step.
If one of the input file is changed, steps needed to take those changes into effect are executed again.

## Python

The Makefile support different modes of Python:

1. Create new virtualenv under `./venv` (default) from a global Python 3. `python3` is expected to be in the PATH.
2. Like (1), but the `VENV_FOLDER` is passed to every *make* call: `make VENV_FOLDER=./some_folder/ install`.
3. `make VENV=off install`: Direct usage of current configure Python 3 environment.
   Like if one uses *pyenv* or another already activated virtual environment, or in CI if the environment is alredy isolated.
4. Like (3), but the environment is not activated, so we need to point *make* to the location with `make VENV=off VENV_FOLDER=~/myenv/myproject_venv` or alike.

**Attention:** if those paramters are used, they *must* be passed to every make call!

**Hint:** Edit the `Makefile` and look for `VENV?=on` (which sets the default). And `VENV_FOLDER?=` (look for the if before) and adjust to your needs.

## Files

`constraints.txt`
    Version pins for your project, used by *pip*.
`README_MAKE.md`
    (this file)
`instance.yaml`
    Zope/Plone application server configuration. Used by *cookiecutter-zope-instance*
`Makefile`
    The configuration for *make*
`requirement.txt`
    The core requirements.
`mx.ini`
    *mxdev* is used to develop with sources from VCS like Git.
    If you need sources from git, add them here.

## Tools

The configuration here uses:

- `make`
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [mxdev](https://pypi.org/project/mxdev)
- [cookiecutter-zope-instance](https://github.com/bluedynamics/cookiecutter-zope-instance/)
