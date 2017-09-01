
""" A plugin to incorporate work-item creation in VSTS
easily out of issues detected from Sentry.io """

from __future__ import absolute_import


import sentry_vsts
import urlparse
from sentry.plugins.bases.issue2 import IssuePlugin2
from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config


class VstsPlugin(CorePluginMixin, IssuePlugin2):
    author = 'Casey Boyle'
    author_url = 'https://github.com/boylec/sentry-vsts'
    version = sentry_vsts.VERSION
    resource_links = [
        ('Bug Tracker', 'https://github.com/boylec/sentry-vsts/issues'),
        ('Source', 'https://github.com/boylec/sentry-vsts'),
    ]

    description = 'Integrate Visual Studio Team Services work \
    items by linking a project.'
    slug = 'vsts'
    title = 'Visual Studio Team Services'
    conf_title = title
    conf_key = slug

    def get_configure_plugin_fields(self, request, project, **kwargs):
        vsts_personal_access_token = self.get_option(
            'vsts_personal_access_token', project)
        secret_field = get_secret_field_config(
            vsts_personal_access_token,
            'Enter your API Personal Access token.'
        )
        secret_field.update(
            {
                'name': 'vsts_personal_access_token',
                'label': 'Access Token',
                'placeholder': 'e.g. g5DWFtLzaztgYFrqhVfE',
                'required': True,
            }
        )

        return [
            {
                'name': 'account',
                'label': 'VSTS Account Name',
                'type': 'text',
                'default': project.organization.name,
                'placeholder': 'e.g. (The same name appearing in your VSTS url: \
                \{name\}.visualstudio.com)',
                'required': True,
                'help': 'Enter the account name of your VSTS instance.'
            },
            {
                'name': 'username',
                'label': 'User name',
                'type': 'text',
                'placeholder': 'e.g. usera',
                'required': True,
                'help': 'Enter your user name.'
            },
            secret_field,
        ]

    def is_configured(self, request, project, **kwargs):
        token = bool(self.get_option('vsts_personal_access_token', project))
        account = bool(self.get_option('account', project))
        username = bool(self.get_option('username', project))
        return token and account and username

    def get_issue_url(self, group, issue_id, **kwargs):
        """
        Given an issue_id (string) return an absolute URL to the issue's
        details page.
        """
        host = self.get_option('host', group.project)
        return urlparse.urljoin(host, 'T%s' % issue_id)

    def create_issue(self, request, group, form_data, **kwargs):
        """
        Creates the issue on the remote service and returns an issue ID.
        """
        raise NotImplementedError

    def get_new_issue_fields(self, request, group, event, **kwargs):
        """
        If overriding, supported properties include 'readonly': true
        """

        orgName = group.project.organization.name
        projName = group.project.name
        grpId = group.short_id
        rootUrl = 'https://sentry.io/'
        absolutePath = rootUrl + orgName + '/' + projName + '/issues/' + grpId

        fields = [
            {
                'name': 'title',
                'label': 'Title',
                'default': self.get_group_title(request, group, event),
                'type': 'text'
            }, {
                'name': 'description',
                'label': 'Description',
                'default': self.get_group_description(request, group, event),
                'type': 'textarea'
            }, {
                'name': 'sentryissuelink',
                'label': 'Sentry Issue Link',
                'default': absolutePath,
                'type': 'url',
                'readonly': True
            },
        ]

        return fields
