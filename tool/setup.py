

setup(
    name='tool',
    version='0.1',
    license='Apache License 2.0',
    include_package_data=True,
    install_requires=['ansible', 'networkx', 'pyyaml', 'argparse'],
    entry_points="""
    [console_scripts]
    tool=tool.main:main
    """,
)
