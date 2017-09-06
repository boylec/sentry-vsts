from __future__ import absolute_import

"""client to interact with VSTS instance - most request code
is reused code from the JIRA plugin maintained by the
Sentry.io team"""

import logging
import six
import base64
from simplejson import _default_decoder

import requests
from requests.exceptions import ConnectionError, RequestException

from simplejson.decoder import JSONDecodeError
from BeautifulSoup import BeautifulStoneSoup


class VSTSError(Exception):
    status_code = None

    def __init__(self, response_text, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        self.text = response_text
        self.xml = None
        if response_text:
            try:
                self.json = _default_decoder.decode(response_text)
            except (JSONDecodeError, ValueError):
                if self.text[:5] == "<?xml":
                    # perhaps it's XML?
                    self.xml = BeautifulStoneSoup(self.text)
                # must be an awful code.
                self.json = None
        else:
            self.json = None
        super(VSTSError, self).__init__(response_text[:128])

    @classmethod
    def from_response(cls, response):
        return cls(response.text, response.status_code)


class VSTSUnauthorized(VSTSError):
    status_code = 401


class VSTSResponse(object):
    def __init__(self, response_text, status_code):
        self.text = response_text
        self.xml = None
        if response_text:
            try:
                self.json = _default_decoder.decode(response_text)
            except (JSONDecodeError, ValueError):
                if self.text[:5] == "<?xml":
                    # perhaps it's XML?
                    self.xml = BeautifulStoneSoup(self.text)
                # must be an awful code.
                self.json = None
        else:
            self.json = None
        self.status_code = status_code

    def __repr__(self):
        return "<VSTSResponse<%s> %s>" % (self.status_code, self.text[:120])

    @classmethod
    def from_response(cls, response):
        return cls(response.text, response.status_code)


class VstsClient(object):
    HTTP_TIMEOUT = 5
    ApiVersion = "3.0"

    def __init__(self, account, projectname, username, secret):
        self.secret = secret
        self.username = username
        self.instance = "{0}.visualstudio.com".format(account)
        self.project = projectname

    def create_work_item(self, title, description, link):
        payload = [
            {
                'op': 'add',
                'path': '/fields/System.Title',
                'value': title,
            },
            {
                'op': 'add',
                'path': '/fields/System.Description',
                'value': description
            },
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "Hyperlink",
                    "url": link,
                }
            }
        ]

        area = "wit"
        resource = "workitems"
        workItemType = "Bug"

        routeTemplate = "https://{0}/{1}/_apis/{2}/{3}/${4}?api-version={5}"
        route = routeTemplate.format(
            self.instance,
            self.project,
            area,
            resource,
            workItemType,
            self.ApiVersion)

        vstsResponse = self.make_request('patch', route, payload=payload)
        return vstsResponse

    def make_request(self, method, route, payload):
        rawSecret = "{0}:{1}".format(self.username, self.secret)
        b64secret = base64.b64encode(rawSecret)
        headers = {
            'Authorization': 'Basic {0}'.format(b64secret),
            'Accept': 'application/json',
            'Content-Type': 'application/json-patch+json'
        }

        try:
            if method == 'patch':
                r = requests.patch(
                    route,
                    json=payload,
                    headers=headers,
                    timeout=self.HTTP_TIMEOUT)
        except ConnectionError as e:
            raise VSTSError(six.text_type(e))
        except RequestException as e:
            resp = e.response
            if not resp:
                raise VSTSError('Internal Error')
            if resp.status_code == 401:
                raise VSTSUnauthorized.from_response(resp)
            raise VSTSError.from_response(resp)
        except Exception as e:
            logging.error(
                'Error in request to %s: %s',
                self.route,
                e.message[:128],
                exc_info=True)
            raise VSTSError('Internal error', 500)

        if r.status_code == 401:
            raise VSTSUnauthorized.from_response(r)
        elif r.status_code < 200 or r.status_code >= 300:
            raise VSTSError.from_response(r)
        return VSTSResponse.from_response(r).json
