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
import mock
import os
import shutil

import pytest

from solar.core.resource.repository import Repository
from solar.core.resource.repository import RepositoryException
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


def generate_structure(target, versions='1.0.0', r_type=0,
                       versions_meta=None, number=3):
    if isinstance(versions, basestring):
        versions = (versions)
    elif isinstance(versions, int):
        versions = _VERSIONS[:versions]

    versions_meta = versions_meta or versions

    if r_type == 0:
        for name in ('first', 'second', 'third')[:number]:
            for version_meta, version in zip(versions_meta, versions):
                cnt = _META_CONTENT.format(version_meta, version, name)
                fp = os.path.join(target, name, version)
                os.makedirs(fp)
                with open(os.path.join(fp, 'meta.yaml'), 'wb') as f:
                    f.write(cnt)
    else:
        for name in ('first', 'second', 'third')[:number]:
            for version_meta, version in zip(versions_meta, versions):
                cnt = _VR_CONTENT.format(version_meta)
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
        if t == RES_TYPE.Composer:
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
    if r_type == RES_TYPE.Composer:
        q = repo_w._list_source_contents(rp + '/first/0.0.1/first.yaml')
        assert len(q) == 1
        _correct_structure_listing(q)


def test_create_empty():
    repo = Repository('empty')
    repo.create()
    assert 'empty' in Repository.list_repos()


@mock.patch('solar.core.resource.repository.Repository._add_contents')
@mock.patch('tempfile.mkdtemp')
@mock.patch('shutil.rmtree')
def test_create_from_src_failed(mock_rmtree, mock_mkdtemp, mock_add_contents):
    tmp_dir = '/tmp/dir'
    mock_mkdtemp.return_value = tmp_dir

    mock_add_contents.side_effect = Exception()
    repo = Repository('fail_create')
    real_path = repo.fpath
    with pytest.raises(Exception):
        repo.create(source='source')

    mock_rmtree.assert_called_with(tmp_dir)
    assert repo.fpath == real_path


@mock.patch('solar.core.resource.repository.Repository._add_contents')
@mock.patch('os.rename')
@mock.patch('tempfile.mkdtemp')
def test_create_from_src(mock_mkdtemp, mock_rename, _):
    tmp_dir = '/tmp/dir'
    mock_mkdtemp.return_value = tmp_dir

    repo = Repository('create_from_src')
    real_path = repo.fpath

    repo.create(source='source')

    mock_rename.assert_called_with(tmp_dir, real_path)
    assert repo.fpath == real_path


def test_detect_invalid_version_in_dir(repo_w, tmpdir):
    rp = str(tmpdir) + '/r1'
    generate_structure(rp, ['0.1.0', '0.1'], number=1)
    repo = Repository("repo_in_dir")
    with pytest.raises(RepositoryException) as ex:
        repo.create(rp)
    assert 'r1/first' in str(ex)


def test_detect_invalid_version_in_meta(repo_w, tmpdir):
    rp = str(tmpdir) + '/r1'
    generate_structure(rp, ['0.1.0'], versions_meta=['0.1'], number=1)
    repo = Repository('repo_in_meta')
    with pytest.raises(RepositoryException) as ex:
        repo.create(rp)
    assert 'r1/first/0.1.0' in str(ex)
