import click

@click.group()
def cli():
    pass


def validate_class(ctx, param, value):
    supported = ('tcp', )
    if not value in supported:
        raise click.BadParameter("%r is not one of %r" % (value, supported))
    return value


@cli.command()
@click.option('--base', default='tcp', callback=validate_class, type=str)
@click.option('--port', default=5555, type=int)
def run(base, port):
    if base == 'tcp':
        from solard.tcp_server import SolardTCPServer
        runner = SolardTCPServer.run_solard
    runner(port)


if __name__ == '__main__':
    cli()
