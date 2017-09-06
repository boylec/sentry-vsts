"""
sentry_vsts
~~~~~~~~~~~~~
:copyright: (c) 2017 by Casey Boyle.
:license: BSD, see LICENSE for more details.
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry_vsts').version
except Exception as e:
    VERSION = 'unknown'
