# -*- coding: utf-8 -*-
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import defaultdict

import errno
import os
import re
import semver
import shutil


from enum import Enum
from solar import utils


RES_TYPE = Enum("Resource Types", 'Normal Virtual')


class RepositoryException(Exception):
    pass


class ResourceNotFound(RepositoryException):

    def __init__(self, spec):
        self.message = 'Resource definition %r not found' % spec

    def __str__(self):
        return str(self.message)


def read_meta(base_path):
    base_meta_file = os.path.join(base_path, 'meta.yaml')

    metadata = utils.yaml_load(base_meta_file)
    metadata.setdefault('version', '1.0.0')
    metadata['base_path'] = os.path.abspath(base_path)
    actions_path = os.path.join(metadata['base_path'], 'actions')
    metadata['actions_path'] = actions_path
    metadata['base_name'] = os.path.split(metadata['base_path'])[-1]

    return metadata


class RepositoryExists(RepositoryException):
    pass


class Repository(object):

    db_obj = None
    _REPOS_LOCATION = '/var/lib/solar/repositories'

    def __init__(self, name):
        self.name = name
        # TODO: (jnowak) sanitize name
        self.fpath = self.repo_path(self.name)

    def _list_source_contents(self, source):
        for pth in os.listdir(source):
            single_path = os.path.join(source, pth)
            if pth.endswith('.yaml'):
                pth = pth[:-5]
                yield RES_TYPE.Virtual, pth, single_path
            elif os.path.exists(os.path.join(single_path, 'meta.yaml')):
                yield RES_TYPE.Normal, pth, single_path
            else:
                if not os.path.isdir(single_path):
                    continue
                for single in os.listdir(single_path):
                    if single.endswith('.yaml'):
                        fp = os.path.join(single_path, single)
                        yield RES_TYPE.Virtual, pth, fp
                    else:
                        try:
                            semver.parse(single)
                        except ValueError:
                            fp = os.path.join(single_path, single)
                            raise RepositoryException("Invalid repository"
                                                      "content: %r" % fp)
                        else:
                            fp = os.path.join(single_path, single)
                            if os.path.exists(os.path.join(fp, 'meta.yaml')):
                                yield RES_TYPE.Normal, pth, fp

    @classmethod
    def repo_path(cls, repo_name):
        return os.path.join(cls._REPOS_LOCATION, repo_name)

    def create(self, source, link_only=False):
        if not link_only:
            try:
                os.mkdir(self.fpath)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    raise RepositoryExists("Repository %s exists" % self.name)
                else:
                    raise
            self._add_contents(source)
        else:
            os.symlink(source, self.fpath)

    def update(self, source, overwrite=False):
        self._add_contents(source, overwrite)

    def _add_contents(self, source, overwrite=False):
        cnts = self._list_source_contents(source)
        for res_type, single_name, single_path in cnts:
            if res_type is RES_TYPE.Normal:
                self.add_single_normal(single_name, single_path, overwrite)
            else:
                self.add_single_vr(single_name, single_path, overwrite)

    def add_single(self, name, source, overwrite=False):
        if os.path.isfile(source):
            return self.add_single_vr(name, source, overwrite)
        return self.add_single_normal(name, source, overwrite)

    def add_single_normal(self, name, source, overwrite=False):
        try:
            metadata = read_meta(source)
        except IOError as e:
            if e.errno == errno.ENOENT:
                raise RepositoryException(
                    "meta.yaml not found: %s" % e.filename)
            raise
        version = metadata['version']
        # TODO: (jnowak) sanitize version
        target_path = os.path.join(self.fpath, name, version)
        try:
            shutil.copytree(source, target_path, symlinks=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            if not overwrite:
                raise
            shutil.rmtree(target_path)
            shutil.copytree(source, target_path, symlinks=True)

    def add_single_vr(self, name, source, overwrite=False):
        # with open(source, 'rb') as f:
        #     parsed = yaml.safe_load(f.read())
        # version = parsed.get('version', '1.0.0')
        version = '1.0.0'
        with open(source, 'rb') as f:
            data = f.read()
        regex = re.compile('^version.*\:(?P<version>.+)')
        m = regex.search(data)
        if m:
            v_file = m.group("version")
            if v_file:
                version = v_file
        target_dir = os.path.join(self.fpath, name, version)
        target_path = os.path.join(target_dir, "{}.yaml".format(name))
        os.makedirs(target_dir)
        try:
            shutil.copy(source, target_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            if not overwrite:
                raise
            shutil.rm(target_dir)
            shutil.copy(source, target_path)

    def remove(self):
        shutil.rmtree(self.fpath)

    def remove_single(self, spec):
        spec = self._parse_spec(spec)
        if spec['version_sign'] != '==':
            raise RepositoryException("Removal possible only with `==` sign")
        path = self._make_version_path(spec)
        shutil.rmtree(path)
        return True

    def iter_contents(self, resource_name=None):

        def _single(single_path):
            try:
                for version in os.listdir(os.path.join(self.fpath,
                                                       single_path)):
                    yield {"name": single_path,
                           'version': version}
            except OSError:
                return

        if resource_name is None:
            for single in os.listdir(self.fpath):
                for gen in _single(single):
                    yield gen
        else:
            for gen in _single(resource_name):
                yield gen

    def get_contents(self, resource_name=None):
        out = defaultdict(list)
        cnt = self.iter_contents(resource_name)
        for curr in cnt:
            out[curr['name']].append(curr['version'])
        return out

    @classmethod
    def _parse_spec(cls, spec):
        if isinstance(spec, dict):
            return spec
        if ':' in spec:
            repos, version = spec.split(':', 1)
        else:
            repos = spec
            version = None
        if '/' in repos:
            repo_name, resource_name = repos.split('/', 1)
        else:
            repo_name = 'resources'
            resource_name = repos
        if version is None:
            version_sign = ">="
        elif '>=' in version or '<=' in version or '==' in version:
            version_sign = version[:2]
            version = version[2:]
        elif '>' in version or '<' in version:
            version_sign = version[:1]
            version = version[1:]
        else:
            version_sign = '=='
        return {'repo': repo_name,
                'resource_name': resource_name,
                'version': version,
                'version_sign': version_sign}

    def _get_version(self, spec):
        spec = self._parse_spec(spec)
        version = spec['version']
        version_sign = spec['version_sign']
        resource_name = spec['resource_name']
        if version_sign == '==':
            return os.path.join(self.fpath, spec['resource_name'], version)
        found = self.iter_contents(resource_name)
        if version is None:
            sc = semver.compare
            sorted_vers = sorted(found,
                                 cmp=lambda a, b: sc(a['version'],
                                                     b['version']),
                                 reverse=True)
            if not sorted_vers:
                raise ResourceNotFound(spec)
            version = sorted_vers[0]['version']
        else:
            version = '{}{}'.format(version_sign, version)
            matched = filter(lambda x: semver.match(x['version'], version),
                             found)
            sorted_vers = sorted(matched,
                                 cmp=lambda a, b: semver.compare(a['version'],
                                                                 b['version']),
                                 reverse=True)
            version = next((x['version'] for x in sorted_vers
                            if semver.match(x['version'], version)),
                           None)
        if version is None:
            raise ResourceNotFound(spec)
        return version

    def _make_version_path(self, spec, version=None):
        spec = self._parse_spec(spec)
        if version is None:
            version = self._get_version(spec)
        return os.path.join(self.fpath, spec['resource_name'], version)

    def read_meta(self, spec):
        path = self.get_path(spec)
        return read_meta(path)

    def get_path(self, spec):
        spec = self._parse_spec(spec)
        return self._make_version_path(spec)

    @classmethod
    def get_metadata(cls, spec):
        spec = cls._parse_spec(spec)
        repo = Repository(spec['repo'])
        return repo.read_meta(spec)

    @classmethod
    def contains(cls, spec):
        repo, spec = cls.parse(spec)
        try:
            version = repo._get_version(spec)
            path = repo._make_version_path(spec, version=version)
        except ResourceNotFound:
            return False
        return os.path.exists(path)

    @classmethod
    def what_version(cls, spec):
        repo, spec = cls.parse(spec)
        try:
            version = repo._get_version(spec)
            path = repo._make_version_path(spec, version=version)
        except ResourceNotFound:
            return False
        if not os.path.exists(path):
            return False
        return version

    @classmethod
    def list_repos(cls):
        return filter(lambda x:
                      os.path.isdir(os.path.join(cls._REPOS_LOCATION,
                                                 x)),
                      os.listdir(cls._REPOS_LOCATION))

    @classmethod
    def parse(cls, spec):
        spec = cls._parse_spec(spec)
        return Repository(spec['repo']), spec

    def is_virtual(self, spec):
        return os.path.exists(self.get_virtual_path(spec))

    def get_virtual_path(self, spec):
        spec = self._parse_spec(spec)
        p = self.get_path(spec)
        return os.path.join(p, "{}.yaml".format(spec['resource_name']))
