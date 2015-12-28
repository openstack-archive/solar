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

import itertools
import os
import pytest
import shutil
from solar.core.resource.repository import Repository
from solar.core.resource.repository import RES_TYPE


Repository._REPOS_LOCATION = '/tmp'


_META_CONTENT = """
handler: null
version: {0}
input:
  a:
    value: 1
    schema: int!
  name:
    value: {1}
  version:
    value: {0}
"""


_VR_CONTENT = """
version: {0}
resources: []"""


_VERSIONS = ('0.0.1', '0.0.2', '1.0.0', '1.4.7', '2.0.0')


def generate_structure(target, versions='1.0.0', r_type=0):
    if isinstance(versions, basestring):
        versions = (versions)
    elif isinstance(versions, int):
        versions = _VERSIONS[:versions]

    if r_type == 0:
        for name in ('first', 'second', 'third'):
            for version in versions:
                cnt = _META_CONTENT.format(version, name)
                fp = os.path.join(target, name, version)
                os.makedirs(fp)
                with open(os.path.join(fp, 'meta.yaml'), 'wb') as f:
                    f.write(cnt)
    else:
        for name in ('first', 'second', 'third'):
            for version in versions:
                cnt = _VR_CONTENT.format(version)
                fp = os.path.join(target, name, version)
                os.makedirs(fp)
                with open(os.path.join(fp, "{}.yaml".format(name)), 'wb') as f:
                    f.write(cnt)


def generator(request, tmpdir_factory):
    try:
        name = request.function.__name__
    except AttributeError:
        # function not available in module-scoped context
        name = "module"
    rp = str(tmpdir_factory.mktemp('{}-resources'.format(name)))
    generate_structure(rp, 3)
    return rp


@pytest.fixture(scope='module', autouse=True)
def repos_path(tmpdir_factory):
    Repository._REPOS_LOCATION = str(tmpdir_factory.mktemp('repositories'))
    return Repository._REPOS_LOCATION


@pytest.fixture(scope="function")
def ct(request, tmpdir_factory):
    p = generator(request, tmpdir_factory)
    request.addfinalizer(lambda: shutil.rmtree(p))
    return p


@pytest.fixture(scope="module")
def repo_r(request, tmpdir_factory):
    path = generator(request, tmpdir_factory)
    r = Repository('rtest')
    r.create(path)
    return r


@pytest.fixture(scope='function')
def repo_w(request, tmpdir_factory):
    path = generator(request, tmpdir_factory)
    r = Repository('rwtest')
    r.create(path)
    request.addfinalizer(lambda: shutil.rmtree(path))
    request.addfinalizer(lambda: r.remove())
    return r


def test_simple_create(ct):
    r = Repository('test')
    r.create(ct)
    for k, v in r.get_contents().items():
        assert len(v) == 3


@pytest.mark.parametrize('spec, exp',
                         (('rtest/first:0.0.1', True),
                          ('rtest/first:0.0.5', False),
                          ('invalid/first:0.0.5', False),
                          ('invalid/first:0.0.1', False)))
def test_simple_select(repo_r, spec, exp):
    spec = Repository._parse_spec(spec)
    assert Repository.contains(spec) is exp
    if exp:
        metadata = Repository.get_metadata(spec)
        assert metadata['version'] == spec['version']
        assert spec['version_sign'] == '=='


@pytest.mark.parametrize('spec, exp',
                         (('rtest/first', True),
                          ('invalid/first', False)))
def test_get_latest(repo_r, spec, exp):
    spec = Repository._parse_spec(spec)
    assert spec['version'] is None
    assert Repository.contains(spec) is exp
    if exp:
        Repository.get_metadata(spec)
        assert spec['version_sign'] == '>='


@pytest.mark.parametrize('spec, exp, exp_ver',
                         (('rtest/first:0.0.1', True, '0.0.1'),
                          ('rtest/first:==0.0.1', True, '0.0.1'),
                          ('rtest/first:==0.0.1', True, '0.0.1'),
                          ('rtest/first:<=0.0.5', True, '0.0.2'),
                          ('rtest/first:>=0.0.5', True, '1.0.0'),
                          ('rtest/first:>=1.0.0', True, '1.0.0')))
def test_guess_version_sharp(repo_r, spec, exp, exp_ver):
    assert Repository.contains(spec) is exp
    if exp:
        metadata = Repository.get_metadata(spec)
        assert metadata['version'] == exp_ver


@pytest.mark.parametrize('spec, exp, exp_ver',
                         (('rtest/first:<0.0.1', False, ''),
                          ('rtest/first:<0.0.2', True, '0.0.1'),
                          ('rtest/first:<0.0.5', True, '0.0.2'),
                          ('rtest/first:>0.0.5', True, '1.0.0'),
                          ('rtest/first:>1.0.0', False, '')))
def test_guess_version_soft(repo_r, spec, exp, exp_ver):
    assert Repository.contains(spec) is exp
    if exp:
        metadata = Repository.get_metadata(spec)
        assert metadata['version'] == exp_ver


@pytest.mark.parametrize('spec', ('rwtest/first:0.0.1',
                                  'rwtest/first:==0.0.1'))
def test_remove_single(repo_w, spec):
    assert Repository.contains(spec)
    repo_w.remove_single(spec)
    assert Repository.contains(spec) is False


def test_two_repos(tmpdir):
    rp1 = str(tmpdir) + '/r1'
    rp2 = str(tmpdir) + '/r2'
    generate_structure(rp1, 2)
    generate_structure(rp2, 5)
    r1 = Repository('repo1')
    r1.create(rp1)
    r2 = Repository('repo2')
    r2.create(rp2)
    exp = set(['repo1', 'repo2'])
    got = set(Repository.list_repos())
    assert got.intersection(exp) == exp
    assert Repository.contains('repo1/first:0.0.1')
    assert Repository.contains('repo2/first:0.0.1')
    assert Repository.contains('repo1/first:2.0.0') is False
    assert Repository.contains('repo2/first:2.0.0')

    r2.remove()
    exp = set(['repo1'])
    got = set(Repository.list_repos())
    assert got.intersection(exp) == exp
    assert Repository.contains('repo2/first:2.0.0') is False


def test_update(repo_w, tmpdir):
    rp = str(tmpdir) + '/second'
    generate_structure(rp, 2)
    with pytest.raises(OSError):
        repo_w.update(rp)
    repo_w.update(rp, overwrite=True)


def _correct_structure_listing(data):
    for curr in data:
        t = curr[0]
        assert curr[1] in ('first', 'second', 'third')
        if t == RES_TYPE.Virtual:
            assert curr[2].endswith('.yaml')


@pytest.mark.parametrize('num, r_type', itertools.product((1, 2, 3), RES_TYPE))
def test_correct_listing(repo_w, tmpdir, num, r_type):
    rp = str(tmpdir) + '/listing'
    generate_structure(rp, num, r_type)
    q = repo_w._list_source_contents(rp)
    assert len(q) == num * 3
    _correct_structure_listing(q)
    q = repo_w._list_source_contents(rp + '/first')
    assert len(q) == num
    _correct_structure_listing(q)
    q = repo_w._list_source_contents(rp + '/first/0.0.1')
    assert len(q) == 1
    _correct_structure_listing(q)
    if r_type == RES_TYPE.Virtual:
        q = repo_w._list_source_contents(rp + '/first/0.0.1/first.yaml')
        assert len(q) == 1
        _correct_structure_listing(q)


def test_create_empty():
    repo = Repository('empty')
    repo.create()
    assert 'empty' in Repository.list_repos()
