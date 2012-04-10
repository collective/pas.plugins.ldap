# TEMPORARY MONKEY PATCH
# until this is changed upstream!

from StringIO import StringIO
from OFS.Image import Image
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
    member = self.getMemberById(userid)
    if member:
        user = member.getUser()
        for sheetname in user.listPropertysheets():
            sheet = user.getPropertysheet(sheetname)
            if 'portrait' in sheet.propertyIds():
               portrait = sheet.getProperty('portrait')
               break
        if portrait is not None:
            # turn into OFS.Image
            sio = StringIO()
            sio.write(portrait)
            content_type = 'image/jpeg' # XXX sniff it
            portrait = Image(userid, user.getProperty('fullname'), sio, content_type)
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
