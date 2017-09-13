Sentry-VSTS
===============

This is a plugin that can be installed on a Sentry.io server which is intended
to allow a Sentry.io user to integrate issues reported in Sentry.io with Visual
Studio Team Services work items.


Installation
============

Install the plugin via ``pip``:

  pip install sentry-vsts


Or optionally install directly from github:

  sudo -H pip install -e git+https://github.com/boylec/sentry-vsts#egg=sentry_vsts

Once the plugin is installed, it will be configurable on a per-project basis
within the Sentry.io UI. (Choose a project to integrate, and then go to project
settings in the top right, and find the Visual Studio Team Services Plugin.
Click configure and fill in configuration fields as needed.)
