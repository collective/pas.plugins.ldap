import logging
from plone.app.users.browser import personalpreferences
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _


logger = logging.getLogger('pas.plugins.ldap')


def description(self):
    """Patch -> pass self.userid always as unicode (L18).
    """
    mt = getToolByName(self.context, 'portal_membership')
    if self.userid and (self.userid != mt.getAuthenticatedMember().id):
        #editing someone else's profile
        return _(u'description_personal_information_form_otheruser',
                 default='Change personal information for $name',
                 mapping={'name': self.userid.decode('utf-8')})
    else:
        #editing my own profile
        return _(u'description_personal_information_form',
                 default='Change your personal information')

personalpreferences.UserDataPanel.description = property(description)


logger.warning(u'PATCHING! -> plone.app.users.browser.personalpreferences.UserDataPanel.description')