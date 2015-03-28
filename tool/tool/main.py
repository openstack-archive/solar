
import sys

import argparse
import yaml

from tool.profile_handlers import process


def parse():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-p',
        '--profile',
        help='profile file',
        required=True)

    parser.add_argument(
        '-r',
        '--resources',
        help='resources dir',
        required=True)

    return parser.parse_args()


def main():
    args = parse()

    with open(args.config) as f:
        profile = yaml.load(f)

    return process(profile, resources)
