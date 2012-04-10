# TEMPORARY MONKEY PATCH
# until this is changed upstream!

from StringIO import StringIO
from zope.component import getUtility
from OFS.Image import Image
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.membership import (
    MembershipTool,
    default_portrait,
)

def patched_getPersonalPortrait(self, id=None, verifyPermission=0):
    """Return a members personal portait.

    Modified from CMFPlone version to URL-quote the member id.
    """
    # XXX eeek, id is built-in, dont use as identifier
    userid = id
    if not userid:
        userid = self.getAuthenticatedMember().getId()
    portrait = None
    site = getUtility(ISiteRoot)
    user = site.acl_users.getUser(userid)
    if user:
        for sheetname in user.listPropertysheets():
            sheet = user.getPropertySheet(sheetname)
            if 'portrait' in sheet:
               portrait = sheet['portrait']
            break
        if portrait is not None:
            # turn into OFS.Image
            sio = StringIO()
            sio.write(portrait)
            content_type = 'image/jpeg' # XXX sniff it
            portrait = Image(id=userid, file=sio, content_type)
            return portrait

    # fallback to memberdata
    safe_id = self._getSafeMemberId(userid)
    membertool = getToolByName(self, 'portal_memberdata')
    portrait = membertool._getPortrait(safe_id)
    if isinstance(portrait, str):
        portrait = None
    if portrait is not None:
        if verifyPermission and not _checkPermission('View', portrait):
            # Don't return the portrait if the user can't get to it
            portrait = None
    if portrait is None:
        portal = getToolByName(self, 'portal_url').getPortalObject()
        portrait = getattr(portal, default_portrait, None)

    return portrait

MembershipTool.getPersonalPortrait = patched_getPersonalPortrait
