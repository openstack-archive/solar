#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def __init_logger():
    logger = logging.getLogger("Wassi")
    logger.setLevel(logging.DEBUG)

    # formatter = logging.Formatter(
    #     '%(levelname)s:%(asctime)s - %(name)s - %(message)s')

    formatter = logging.Formatter('%(levelname)s:%(asctime)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger


__global_logger = None


def get_logger():
    global __global_logger
    if not __global_logger:
        __global_logger = __init_logger()
        return __global_logger

logger = get_logger()
