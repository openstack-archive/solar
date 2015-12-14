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

import click
import os
import yaml

from solar.core.resource.repository import Repository
from solar.core.resource.repository import RepositoryExists


@click.group()
def repository():
    pass


@repository.command()
@click.option('--repository', '-r', default=None)
def show(repository):
    if not repository:
        repos = Repository.list_repos()
        str_repos = '\n'.join(sorted(repos))
        click.echo(str_repos)
    else:
        repo = Repository(repository)
        content = yaml.safe_dump(dict(repo.get_contents()),
                                 default_flow_style=False)
        click.echo_via_pager(content)


@repository.command(name='import')
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.option('--name', '-n', default=None)
@click.option('--link', '-l', is_flag=True, default=False)
def _import(name, source, link):
    if name is None:
        name = os.path.split(source)[-1]
    repo = Repository(name)
    try:
        repo.create(source, link)
    except RepositoryExists as e:
        click.echo(click.style(str(e), fg='red'))
    else:
        cnt = len(list(repo.iter_contents()))
        click.echo(
            "Created new repository with {} resources".format(cnt))


@repository.command()
@click.argument('name')
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.option('--overwrite', is_flag=True, default=False)
def update(name, source, overwrite):
    repo = Repository(name)
    prev = len(list(repo.iter_contents()))
    repo.update(source, overwrite)
    now = len(list(repo.iter_contents()))
    diff = now - prev
    click.echo(
        "Updated repository, with {} resources".format(diff))


@repository.command()
@click.argument('name')
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.option('--overwrite', is_flag=True, default=False)
@click.option('--resource_name', type=str, default=None)
def add(name, source, overwrite, resource_name):
    repo = Repository(name)
    if resource_name is None:
        resource_name = os.path.split(source)[-1]
    repo.add_single(name=resource_name,
                    source=source,
                    overwrite=overwrite)


@repository.command()
@click.argument('name')
def remove_repo(name):
    repo = Repository(name)
    repo.remove()


@repository.command()
@click.argument('spec')
def remove(spec):
    repo, spec = Repository.parse(spec)
    repo.remove_single(spec)


@repository.command()
@click.argument('spec')
@click.option('--bool', is_flag=True, default=False)
def contains(spec, bool):
    repo, spec = Repository.parse(spec)
    if bool:
        result = Repository.contains(spec)
        if result:
            click.echo(click.style("Exists", fg='green'))
            return
    else:
        result_version = Repository.what_version(spec)
        if result_version:
            click.echo(click.style("Found: {}".format(result_version),
                                   fg='green'))
            return
    spec_data = yaml.safe_dump(spec, default_flow_style=False)
    click.echo(click.style("Not found: \n{}".format(spec_data),
                           fg='red'))
