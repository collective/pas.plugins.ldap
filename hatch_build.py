"""Hatchling build hook.

Compiles the gettext ``.po`` message catalogs to ``.mo`` at build time and
force-includes them into the built sdist and wheel.

The ``.mo`` files are not kept in version control (they are generated
artifacts, see ``.gitignore``).  Without this hook they would only end up in a
release if ``make gettext-compile`` happened to be run before building, so the
Spanish translation would silently be missing for end users installing from
PyPI.  Compiling them as part of the build makes the result correct regardless
of how or where the package is built.
"""

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pathlib import Path


LOCALES = Path("src/pas/plugins/ldap/locales")


class CompileCatalogsBuildHook(BuildHookInterface):
    """Compile ``.po`` catalogs to ``.mo`` and include them in the artifact."""

    PLUGIN_NAME = "compile-catalogs"

    def initialize(self, version, build_data):
        from babel.messages.mofile import write_mo
        from babel.messages.pofile import read_po

        root = Path(self.root)
        locales = root / LOCALES
        for po_path in sorted(locales.glob("*/LC_MESSAGES/*.po")):
            mo_path = po_path.with_suffix(".mo")
            with po_path.open("rb") as fh:
                catalog = read_po(fh)
            with mo_path.open("wb") as fh:
                write_mo(fh, catalog)
            # the .mo files are gitignored, so force them into the artifact
            build_data["force_include"][str(mo_path)] = str(mo_path.relative_to(root))
