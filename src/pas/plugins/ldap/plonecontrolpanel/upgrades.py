# -*- coding: utf-8 -*-


def remove_persistent_import_step_from_base_profile(context):
    """Remove broken persistent import step from base profile.

    The base profile (one directory up) had a broken import step,
    so we added an upgrade step to remove it.

    But in Plone, you don't directly install the base profile,
    so we need an upgrade step for the plonecontrolpanel:default profile.
    This calls the upgrade step from base, and updates its profile version.

    A bit double, but then it works cleanly,
    both within Plone and outside of Plone.
    """
    from pas.plugins.ldap.setuphandlers import remove_persistent_import_step

    remove_persistent_import_step(context)
    context.setLastVersionForProfile("pas.plugins.ldap:default", "2")
