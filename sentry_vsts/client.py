from __future__ import absolute_import

"""client to interact with VSTS instance - most request code
is reused code from the JIRA plugin maintained by the
Sentry.io team"""

import logging
import six
import base64

from sentry.http import build_session
from sentry.utils import json
from requests.exceptions import ConnectionError, RequestException

from simplejson.decoder import JSONDecodeError
from BeautifulSoup import BeautifulStoneSoup
from django.utils.datastructures import SortedDict


class VSTSError(Exception):
    status_code = None

    def __init__(self, response_text, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        self.text = response_text
        self.xml = None
        if response_text:
            try:
                self.json = json.loads(
                    response_text,
                    object_pairs_hook=SortedDict
                )
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
                self.json = json.loads(
                    response_text,
                    object_pairs_hook=SortedDict
                )
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
        return "<JIRAResponse<%s> %s>" % (self.status_code, self.text[:120])

    @classmethod
    def from_response(cls, response):
        return cls(response.text, response.status_code)


class VstsClient(object):
    HTTP_TIMEOUT = 5

    def __init__(self, account, projectname, secret):
        routeTemplate = "https://{0}/DefaultCollection/{1}/_apis/wit/workitems/\
                        $Bug?api-version=3.0"
        self.secret = secret
        self.route = routeTemplate.format(account, projectname)

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

        vstsResponse = self.make_request(payload=payload)
        return vstsResponse

    def make_request(self, payload):
        b64secret = base64.b64encode(self.secret)
        headers = {'Authorization': "Basic {0}".format(b64secret)}
        session = build_session()
        try:
            r = session.patch(
                self.route,
                json=payload,
                headers=headers,
                verify=False,
                timeout=self.HTTP_TIMEOUT
            )
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
        return VSTSResponse.from_response(r)
