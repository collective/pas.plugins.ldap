"""Update locales."""

from pathlib import Path

import logging
import re
import subprocess

logger = logging.getLogger("i18n")
logger.setLevel(logging.DEBUG)


PATTERN = r"^[a-z]{2}.*"

locale_path = Path(__file__).parent.resolve()
target_path = locale_path.parent.resolve()
domain = "pas.plugins.ldap"

i18ndude = "uvx i18ndude"
lingua = "pot-create"

# ignore node_modules files resulting in errors
excludes = '"*.html *json-schema*.xml"'


def i18n_script_setup():
    """Setup the i18n scripts"""
    cmd_i18ndude = "uvx i18ndude"
    cmd_lingua = "uvx lingua"
    subprocess.call(cmd_i18ndude, shell=True)  # noQA: S602
    subprocess.call(cmd_lingua, shell=True)  # noQA: S602


def locale_folder_setup(domain: str):
    """Create the locales folders

    Args:
        domain (str): locale domain application
    """
    languages = [path for path in locale_path.glob("*") if path.is_dir()]
    for lang_folder in languages:
        lc_messages_path = lang_folder / "LC_MESSAGES"
        lang = lang_folder.name
        if lc_messages_path.exists():
            continue
        elif re.match(PATTERN, lang):
            lc_messages_path.mkdir()
            cmd = (
                f"msginit --locale={lang} "
                f"--input={locale_path}/{domain}.pot "
                f"--output={locale_path}/{lang}/LC_MESSAGES/{domain}.po"
            )
            subprocess.call(cmd, shell=True)  # noQA: S602


def _rebuild(domain: str):
    """Rebuild the pot file from the source code

    Args:
        domain (str): locale domain application
    """
    cmd = (
        f"{i18ndude} rebuild-pot --pot {locale_path}/{domain}.pot "
        f"--exclude {excludes} "
        f"--create {domain} {target_path} {target_path}/plonecontrolpanel"
    )
    subprocess.call(cmd, shell=True)  # noQA: S602


def _rebuild_pot_to_merge():
    """Rebuild pot file to merge"""
    cmd = (
        f"{lingua} {target_path}/properties.yaml "
        f"--output {locale_path}/merge-lingua.pot"
    )
    subprocess.call(cmd, shell=True)  # noQA: S602


def _merge(domain: str):
    """Merge the lingua pot file with the i18ndude pot file

    Args:
        domain (str): locale domain application
    """
    cmd = (
        f"{i18ndude} merge --pot {locale_path}/{domain}.pot "
        f"--merge {locale_path}/merge-lingua.pot"
    )
    subprocess.call(cmd, shell=True)  # noQA: S602


def _sync(domain: str):
    """Sync the po files from the pot file

    Args:
        domain (str): locale domain application
    """
    cmd = (
        f"{i18ndude} sync --pot {locale_path}/{domain}.pot "
        f"{locale_path}/*/LC_MESSAGES/{domain}.po"
    )
    subprocess.call(cmd, shell=True)  # noQA: S602


def main():
    """Main application function"""
    if domain:
        logger.info("Updating translations for %s", domain)
        i18n_script_setup()
        locale_folder_setup(domain)
        _rebuild(domain)
        _rebuild_pot_to_merge()
        _merge(domain)
        _sync(domain)


if __name__ == "__main__":
    main()
