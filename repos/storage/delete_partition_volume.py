#!/usr/bin/env python
"""this test case is used for deleting volume of
   a partition type storage pool from xml
"""

import os
import re
import sys
import commands

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

def usage():
    """usage infomation"""
    print """mandatory options:
              poolname: The name of pool under which the volume to be created
              volname: Name of the volume to be created"""

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""

    mandatory_params = ['poolname', 'volname']

    for param in mandatory_params:
        if param not in params:
            logger.error("%s is required" % param)
            usage()
            return 1
        elif len(params[param]) == 0:
            logger.error("%s value is empty, please inputting a value" % param)
            return 1
        else:
            return 0

def partition_volume_check(poolobj, volname, partition_name):
    """check the newly deleted volume, the way of checking is to
       grep the partition name of the volume in /proc/partitions
       to ensure its non-existence"""

    shell_cmd = "grep %s /proc/partitions" % partition_name
    logger.debug("excute the shell command %s to \
                  check the newly created partition" % shell_cmd)

    stat, ret = commands.getstatusoutput(shell_cmd)
    if stat != 0 and volname not in poolobj.listVolumes():
        return 0
    else:
        return 1

def virsh_vol_list(poolname):
    """using virsh command list the volume information"""

    shell_cmd = "virsh vol-list %s" % poolname
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug(text)


def delete_partition_volume(params):
    """delete a volume in the disk type of pool"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if not params_check_result:
        logger.info("Params are right")
    else:
        logger.error("Params are wrong")
        return 1

    poolname = params.pop('poolname')
    volname = params['volname']

    logger.info("the poolname is %s, volname is %s" % (poolname, volname))

    uri = params['uri']

    conn = libvirt.open(uri)

    storage_pool_list = conn.listStoragePools()

    if poolname not in storage_pool_list:
        logger.error("pool %s doesn't exist or not running")
        return return_close(conn, logger, 1)

    poolobj = conn.storagePoolLookupByName(poolname)

    logger.info("before deleting a volume, \
                 current volume list in the pool %s is %s" % \
                 (poolname, poolobj.listVolumes()))

    logger.info("and using virsh command to \
                 ouput the volume information in the pool %s" % poolname)
    virsh_vol_list(poolname)

    volobj = poolobj.storageVolLookupByName(volname)
    volpath = volobj.path()
    logger.debug("the path of volume is %s" % volpath)

    partition_name = volpath.split("/")[-1]

    try:
        logger.info("delete volume %s" % volname)
        volobj.delete(0)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return return_close(conn, logger, 1)

    logger.info("delete volume successfully, and output the volume information")
    logger.info("after deleting a volume, \
                 current volume list in the pool %s is %s" % \
                 (poolname, poolobj.listVolumes()))
    virsh_vol_list(poolname)

    logger.info("Now, check the validation of deleting volume")
    check_res = partition_volume_check(poolobj, \
                                       volname, partition_name)

    if not check_res:
        logger.info("checking succeed")
        return return_close(conn, logger, 0)
    else:
        logger.error("checking failed")
        return return_close(conn, logger, 1)
