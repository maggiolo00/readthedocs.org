from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import logging
import re

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


def project_and_path_from_request(request, path):
    if hasattr(request, 'slug'):
        project_slug = request.slug
    elif path.startswith('/docs/'):
        # In this case we use the docs without subdomains. So let's strip the
        # docs prefix.
        match = re.match(
            r'^/docs/(?P<project_slug>[^/]+)(?P<path>/.*)$',
            path)
        project_slug = match.groupdict()['project_slug']
        path = match.groupdict()['path']
    else:
        return None, path

    try:
        project = Project.objects.get(slug=project_slug)
    except Project.DoesNotExist:
        return None, path
    return project, path


def language_and_version_from_path(path):
    match = re.match(
        r'^/(?P<language>[^/]+)/(?P<version_slug>[^/]+)(?P<path>/.*)$',
        path)
    if match:
        language = match.groupdict()['language']
        version_slug = match.groupdict()['version_slug']
        path = match.groupdict()['path']
        return language, version_slug, path
    return None, None, path


def get_redirect_response(request, path):
    project, path = project_and_path_from_request(request, path)
    if not project:
        return None

    language = None
    version = None
    if not project.single_version:
        language, version_slug, path = language_and_version_from_path(path)
        if version_slug:
            try:
                version = project.versions.get(slug=version_slug)
            except Version.DoesNotExist:
                pass

    new_path = project.redirects.get_redirect_path(
        path=path, project=project, version=version)

    if new_path is None:
        return None

    # Re-use the domain and protocol used in the current request.
    # Redirects shouldn't change the domain, version or language.
    new_path = request.build_absolute_uri(new_path)
    return HttpResponseRedirect(new_path)
