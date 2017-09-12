
""" A plugin to incorporate work-item creation in VSTS
easily out of issues detected from Sentry.io """

from __future__ import absolute_import

import sentry_vsts
import urllib

from sentry_vsts.client import VstsClient
from sentry.plugins.bases.issue2 import IssuePlugin2
from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config
from sentry.utils.http import absolute_uri


class VstsPlugin(CorePluginMixin, IssuePlugin2):
    allowed_actions = ['create', 'unlink']
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
    title = 'VSTS'
    conf_title = title
    conf_key = slug

    def get_configure_plugin_fields(self, request, project, **kwargs):
        vsts_personal_access_token = self.get_option(
            'vsts_personal_access_token',
            project
        )

        secret_field = get_secret_field_config(
            vsts_personal_access_token,
            'Enter your API Personal Access token. Follow the instructions \
            at the following URL to create a token for yourself in VSTS: \
            https://www.visualstudio.com/en-us/docs/setup-admin/team-services/use-personal-access-tokens-to-authenticate'
        )
        secret_field.update(
            {
                'name': 'vsts_personal_access_token',
                'label': 'Access Token',
                'placeholder': '52 character personal access token',
                'required': True,
            }
        )

        return [
            {
                'name': 'account',
                'label': 'VSTS Account Name',
                'type': 'text',
                'default': project.organization.name,
                'placeholder': '',
                'required': True,
                'help': 'Enter the account name of your VSTS instance. This will be the \
                same name appearing in your VSTS url: i.e. [name].visualstudio.com'
            },
            {
                'name': 'projectname',
                'label': 'Project name',
                'type': 'text',
                'default': project.name,
                'placeholder': '',
                'required': True,
                'help': 'Enter the Visual Studio Team Services project name that you wish \
                new work items to be added to when they are created from Sentry. This must \
                be a valid project name within the VSTS account specified above.'
            },
            {
                'name': 'username',
                'label': 'User name',
                'type': 'text',
                'placeholder': 'e.g. usera',
                'required': True,
                'help': 'Enter your user name.'
            },
            secret_field
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
        account = self.get_option('account', group.project)
        projectname = urllib.quote(
            self.get_option('projectname', group.project))
        queryparams = urllib.urlencode({'id': issue_id})
        template = "https://{0}.visualstudio.com/{1}/_workitems?{2}"
        return template.format(account, projectname, queryparams)

    def create_issue(self, request, group, form_data, **kwargs):
        """
        Creates the issue on the remote service and returns an issue ID.
        """
        account = self.get_option('account', group.project)
        projectname = self.get_option('projectname', group.project)
        username = self.get_option('username', group.project)
        secret = self.get_option('vsts_personal_access_token', group.project)

        client = VstsClient(account, projectname, username, secret)

        title = form_data['title']
        description = form_data['description']
        link = form_data['sentryLink']
        created_item = client.create_work_item(title, description, link)
        return created_item['id']

    def get_group_description(self, request, group, event):
        return self.get_group_body(request, group, event)

    def get_new_issue_fields(self, request, group, event, **kwargs):
        """
        If overriding, supported properties include 'readonly': true
        """
        title = self.get_group_title(request, group, event)
        title = "[Sentry Bug] {0}".format(title)
        fields = [
            {
                'name': 'title',
                'label': 'Title',
                'default': title,
                'type': 'text'
            }, {
                'name': 'description',
                'label': 'Description',
                'default': self.get_group_description(request, group, event),
                'type': 'textarea'
            }, {
                'name': 'sentryLink',
                'label': 'Sentry Issue Link',
                'default': absolute_uri(group.get_absolute_url()),
                'type': 'url',
                'readonly': True
            },
        ]

        return fields
