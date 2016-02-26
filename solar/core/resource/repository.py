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
import tempfile

from enum import Enum
import errno
import os
import semantic_version
import shutil
import yaml

from solar import utils


RES_TYPE = Enum("Resource Types", 'Normal Composer')


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
    # NOTE(jnowak): when `version: 0.1` then it's float
    metadata['version'] = str(metadata['version'])
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
    _TMP_DIRNAME = '.tmp'

    def __init__(self, name):
        self.name = name
        # TODO: (jnowak) sanitize name
        self.fpath = self.repo_path(self.name)

    @classmethod
    def _list_source_contents(cls, source):
        if source.endswith('.yaml'):
            # single CR
            pth = os.path.split(source)[-1][:-5]
            return ((RES_TYPE.Composer, pth, source), )
        elif os.path.isdir(source):
            meta_path = os.path.join(source, 'meta.yaml')
            if os.path.exists(meta_path):
                # single normal
                pth = os.path.split(source)[-1]
                valid = semantic_version.validate(pth)
                if not valid:
                    name = pth
                else:
                    # if it was semver then single_path may look like
                    # /a/b/name/version
                    # and source may look like /a/b/name
                    # we can extract name from this path then
                    name = source.split(os.path.sep)[-2]
                return ((RES_TYPE.Normal, name, source), )
            return tuple(cls._list_source_contents_from_multidir(source))

    @classmethod
    def _list_source_contents_from_multidir(cls, source):
        for pth in os.listdir(source):
            single_path = os.path.join(source, pth)
            if pth.endswith('.yaml'):
                pth = pth[:-5]
                yield RES_TYPE.Composer, pth, single_path
            elif os.path.exists(os.path.join(single_path, 'meta.yaml')):
                valid = semantic_version.validate(pth)
                if not valid:
                    name = pth
                else:
                    # if it was semver then single_path may look like
                    # /a/b/name/version
                    # and source may look like /a/b/name
                    # we can extract name from this path then
                    name = os.path.split(source)[-1]
                yield RES_TYPE.Normal, name, single_path
            else:
                maybe_cr = os.path.join(single_path,
                                        "{}.yaml".format(
                                            os.path.split(source)[-1]))
                if os.path.exists(maybe_cr):
                    name = os.path.split(source)[-1]
                    yield RES_TYPE.Composer, name, maybe_cr
                    continue
                if not os.path.isdir(single_path):
                    continue
                for single in os.listdir(single_path):
                    valid = semantic_version.validate(single)
                    if not valid:
                        fp = os.path.join(single_path, single)
                        raise RepositoryException(
                            "Unexpected repository content "
                            "structure: {} ""Expected directory "
                            "with version number".format(single_path))
                    else:
                        fp = os.path.join(single_path, single)
                        if os.path.exists(os.path.join(fp, 'meta.yaml')):
                            yield RES_TYPE.Normal, pth, fp
                        elif os.path.exists(
                                os.path.join(fp, '{}.yaml'.format(pth))):
                            cr = os.path.join(fp, '{}.yaml'.format(pth))
                            yield RES_TYPE.Composer, pth, cr

    @classmethod
    def repo_path(cls, repo_name):
        return os.path.join(cls._REPOS_LOCATION, repo_name)

    def create(self, source=None, link_only=False):
        if source is None:
            os.mkdir(self.fpath)
            return
        if not link_only:
            if os.path.isdir(self.fpath):
                raise RepositoryExists("Repository %s "
                                       "already exists" % self.name)

            if not os.path.isdir(self.tmp_dir):
                os.makedirs(self.tmp_dir)

            old_fpath = self.fpath
            self.fpath = tempfile.mkdtemp(dir=self.tmp_dir)
            try:
                self._add_contents(source)
                os.rename(self.fpath, old_fpath)
            except Exception as e:
                shutil.rmtree(self.fpath)
                raise
            finally:
                self.fpath = old_fpath
        else:
            try:
                os.symlink(source, self.fpath)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    raise RepositoryExists("Repository %s "
                                           "already exists" % self.name)
                else:
                    raise

    def update(self, source, overwrite=False):
        self._add_contents(source, overwrite)

    def _add_contents(self, source, overwrite=False):
        cnts = self._list_source_contents(source)
        for res_type, single_name, single_path in cnts:
            if res_type is RES_TYPE.Normal:
                self.add_single_normal(single_name, single_path, overwrite)
            else:
                self.add_single_cr(single_name, single_path, overwrite)

    def add_single(self, name, source, overwrite=False):
        if os.path.isfile(source):
            name = name.replace('.yaml', '')
            return self.add_single_cr(name, source, overwrite)
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
        valid = semantic_version.validate(version)
        if not valid:
            raise RepositoryException("Invalid version "
                                      "%s for %s" % (version,
                                                     source))
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

    def add_single_cr(self, name, source, overwrite=False):
        with open(source, 'rb') as f:
            parsed = yaml.safe_load(f.read())
        version = parsed.get('version', '1.0.0')
        target_dir = os.path.join(self.fpath, name, version)
        target_path = os.path.join(target_dir, "{}.yaml".format(name))
        if not os.path.exists(target_dir):
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
            for single in self.list_repos():
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
            sc = semantic_version.compare
            sorted_vers = sorted(found,
                                 cmp=lambda a, b: sc(a['version'],
                                                     b['version']),
                                 reverse=True)
            if not sorted_vers:
                raise ResourceNotFound(spec)
            version = sorted_vers[0]['version']
        else:
            version = '{}{}'.format(version_sign, version)
            matched = filter(lambda x: semantic_version.match(version,
                                                              x['version']),
                             found)
            sorted_vers = sorted(matched,
                                 cmp=lambda a, b: semantic_version.compare(
                                     a['version'],
                                     b['version']),
                                 reverse=True)
            version = next((x['version'] for x in sorted_vers
                            if semantic_version.match(version, x['version'])),
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

    @property
    def tmp_dir(self):
        return os.path.join(self._REPOS_LOCATION, self._TMP_DIRNAME)

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
        return filter(
            lambda x: (os.path.isdir(os.path.join(cls._REPOS_LOCATION, x))
                       and x != cls._TMP_DIRNAME),
            os.listdir(cls._REPOS_LOCATION)
        )

    @classmethod
    def parse(cls, spec):
        spec = cls._parse_spec(spec)
        return Repository(spec['repo']), spec

    def is_composer_file(self, spec):
        return os.path.exists(self.get_composer_file_path(spec))

    def get_composer_file_path(self, spec):
        spec = self._parse_spec(spec)
        p = self.get_path(spec)
        return os.path.join(p, "{}.yaml".format(spec['resource_name']))
