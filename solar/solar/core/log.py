import logging
import sys


log = logging.getLogger('solar')


def setup_logger():
    handler = logging.FileHandler('solar.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s (%(filename)s::%(lineno)s)::%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    print_formatter = logging.Formatter('%(levelname)s (%(filename)s::%(lineno)s)::%(message)s')
    print_handler = logging.StreamHandler(stream=sys.stdout)
    print_handler.setFormatter(print_formatter)
    log.addHandler(print_handler)

    log.setLevel(logging.DEBUG)

setup_logger()