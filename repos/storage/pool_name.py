#!/usr/bin/env python
"""testing "virsh pool-name" function
"""

import os
import sys
import re
import time
import commands

import libvirt
from libvirt import libvirtError

from utils import utils

VIRSH_POOLNAME = "virsh pool-name"

def check_pool_uuid(poolname, UUIDString, logger):
    """ check the output of virsh pool-name """
    status, ret = commands.getstatusoutput(VIRSH_POOLNAME + ' %s' % UUIDString)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_POOLNAME + ' %s' % UUIDString + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        poolname_virsh = ret[:-1]
        logger.debug("poolname from " + VIRSH_POOLNAME + " is %s" % poolname_virsh)
        logger.debug("poolname we expected is %s" % poolname)
        if poolname_virsh == poolname:
            return True
        else:
            return False

def pool_name(params):
    """ get the UUIDString of a pool, then call
        virsh pool-name to generate the name of pool,
        then check it
    """
    logger = params['logger']
    if 'poolname' not in params:
        logger.error("the option poolname is required")
        return 1
    else:
        poolname = params['poolname']

    uri = params['uri']
    conn = libvirt.open(uri)

    logger.info("the uri is %s" % uri)

    pool_names = conn.listDefinedStoragePools()
    pool_names += conn.listStoragePools()

    if poolname in pool_names:
        poolobj = conn.storagePoolLookupByName(poolname)
    else:
        logger.error("%s not found\n" % poolname);
        conn.close()
        return 1

    try:
        try:
            UUIDString = poolobj.UUIDString()
            logger.info("the UUID string of pool %s is %s" % (poolname, UUIDString))
            if check_pool_uuid(poolname, UUIDString, logger):
                logger.info(VIRSH_POOLNAME + " test succeeded.")
                return 0
            else:
                logger.error(VIRSH_POOLNAME + " test failed.")
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
