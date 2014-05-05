# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manages mapping of users to roles and roles to privileges."""

__author__ = 'Pavel Simakov (psimakov@google.com)'

import re

import config
from google.appengine.api import users


GCB_ADMIN_LIST = config.ConfigProperty(
    'gcb_admin_user_emails', str, (
        'A list of email addresses for super-admin users. '
        'WARNING! Super-admin users have the highest level of access to your '
        'Google App Engine instance and to all data about all courses and '
        'students within that instance. Be very careful when modifying this '
        'property.  '
        'Syntax: Entries may be separated with any combination of '
        'tabs, spaces, commas, or newlines.  Existing values using "[" and '
        '"]" around email addresses continues to be supported.  '
        'Regular expressions are not supported.'),
    '', multiline=True)

KEY_COURSE = 'course'
KEY_ADMIN_USER_EMAILS = 'admin_user_emails'

GCB_WHITELISTED_USERS = config.ConfigProperty(
    'gcb_user_whitelist', str, (
        'A list of email addresses of users allowed access to courses.  '
        'If this is blank, site-wide user whitelisting is disabled.  '
        'Access to courses is also implicitly granted to super admins and '
        'course admins, so you need not repeat those names here.  '
        'Course-specific whitelists trump this list - if a course has a '
        'non-blank whitelist, this one is ignored.  '
        'Syntax: Entries may be separated with any combination of '
        'tabs, spaces, commas, or newlines.  Existing values using "[" and '
        '"]" around email addresses continues to be supported.  '
        'Regular expressions are not supported.'),
    '', multiline=True)
EMAIL_LIST_SPLITTER = re.compile(r'[\[\] ,\t\n]+', flags=re.M)


class Roles(object):
    """A class that provides information about user roles."""

    @classmethod
    def is_direct_super_admin(cls):
        """Checks if current user is a super admin, without delegation."""
        return users.get_current_user() and users.is_current_user_admin()

    @classmethod
    def is_super_admin(cls):
        """Checks if current user is a super admin, possibly via delegation."""
        if cls.is_direct_super_admin():
            return True

        user = users.get_current_user()
        if user and user.email() in cls._to_list(GCB_ADMIN_LIST.value):
            return True
        return False

    @classmethod
    def is_course_admin(cls, app_context):
        """Checks if a user is a course admin, possibly via delegation."""
        if cls.is_super_admin():
            return True

        if KEY_COURSE in app_context.get_environ():
            environ = app_context.get_environ()[KEY_COURSE]
            if KEY_ADMIN_USER_EMAILS in environ:
                allowed = environ[KEY_ADMIN_USER_EMAILS]
                user = users.get_current_user()
                if allowed and user and user.email() in cls._to_list(allowed):
                    return True

        return False

    @classmethod
    def is_user_whitelisted(cls, app_context):
        user = users.get_current_user()
        global_whitelist = GCB_WHITELISTED_USERS.value.strip()
        course_whitelist = app_context.whitelist.strip()

        # Most-specific whitelist used if present.
        if course_whitelist:
            return user and user.email() in cls._to_list(course_whitelist)
        # Global whitelist if no course whitelist
        elif global_whitelist:
            return user and user.email() in cls._to_list(global_whitelist)
        # Lastly, no whitelist = no restrictions
        else:
            return True

    @classmethod
    def _to_list(cls, text):
        return [item for item in EMAIL_LIST_SPLITTER.split(text) if item]
