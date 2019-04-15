# -*- coding: utf-8 -*-
# TEMPORARY MONKEY PATCH
# until this is changed upstream!
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.Image import Image
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.membership import _checkPermission
from Products.PlonePAS.tools.membership import default_portrait
from Products.PlonePAS.tools.membership import MembershipTool
from six import StringIO
from zope.interface import implementer
from zope.traversing.interfaces import ITraversable


class PortraitImage(Image):
    def getPhysicalPath(self):
        parent = aq_parent(aq_inner(self))
        trav = "++portrait++%s" % self.id()
        if not hasattr(parent, "getPhysicalPath"):
            return ("", trav)
        return tuple(list(parent.getPhysicalPath()) + [trav])


def getPortraitFromSheet(context, userid):
    mtool = getToolByName(context, "portal_membership")
    member = mtool.getMemberById(userid)
    if not member:
        return None
    user = member.getUser()
    portrait = None
    for sheetname in user.listPropertysheets():
        sheet = user.getPropertysheet(sheetname)
        if "portrait" in sheet.propertyIds():
            portrait = sheet.getProperty("portrait")
            break
    if not portrait:
        # nothing found on sheet
        return None
    # turn into OFS.Image
    sio = StringIO()
    sio.write(portrait)
    content_type = "image/jpeg"  # XXX sniff it
    portrait = PortraitImage(userid, user.getProperty("fullname"), sio, content_type)
    return portrait


@implementer(ITraversable)
class PortraitTraverser(object):
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def traverse(self, userid, subpath):
        return getPortraitFromSheet(self.context, userid).__of__(self.context)


def patched_getPersonalPortrait(self, id=None, verifyPermission=0):
    """Return a members personal portait.

    Modified from CMFPlone version to URL-quote the member id.
    """
    # XXX eeek, id is built-in, dont use as identifier
    userid = id
    if not userid:
        userid = self.getAuthenticatedMember().getId()

    portrait = getPortraitFromSheet(self, userid)
    if portrait:
        return portrait

    # fallback to memberdata
    safe_id = self._getSafeMemberId(userid)
    membertool = getToolByName(self, "portal_memberdata")
    portrait = membertool._getPortrait(safe_id)
    if isinstance(portrait, str):
        portrait = None
    if portrait is not None:
        if verifyPermission and not _checkPermission("View", portrait):
            # Don't return the portrait if the user can't get to it
            portrait = None
    if portrait is None:
        portal = getToolByName(self, "portal_url").getPortalObject()
        portrait = getattr(portal, default_portrait, None)

    return portrait


MembershipTool.getPersonalPortrait = patched_getPersonalPortrait
