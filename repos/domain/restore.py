#!/usr/bin/env python
"""this test case is used for testing
   restore domain from a disk save image
   mandatory arguments: guestname
                        filepath
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import utils

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'filepath' ]
    for key in keys:
        if key not in params:
            logger.error("%s is required" % key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" % key)
            return 1
        else:
            pass

def get_guest_ipaddr(*args):
    """Get guest ip address"""
    (guestname, util, logger) = args

    mac = util.get_dom_mac_addr(guestname)
    logger.debug("guest mac address: %s" % mac)

    ipaddr = util.mac_to_ip(mac, 15)
    logger.debug("guest ip address: %s" % ipaddr)

    if util.do_ping(ipaddr, 20) == 1:
        logger.info("ping current guest successfull")
        return ipaddr
    else:
        logger.error("Error: can't ping current guest")
        return None

def check_guest_status(*args):
    """Check guest current status"""
    (domobj, logger) = args

    state = domobj.info()[0]
    logger.debug("current guest status: %s" % state)

    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
        return False
    else:
        return True

def check_guest_restore(*args):
    """Check restore domain result, if restore domain is successful,
       guest status will not be paused and can be ping
    """
    (guestname, domobj, util, logger) = args

    if check_guest_status(domobj, logger):
        if get_guest_ipaddr(guestname, util, logger):
            return True
        else:
            return False
    else:
        return False

def restore(params):
    """Save domain to a disk file"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    filepath = params['filepath']
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(guestname)

    if check_guest_status(domobj, logger):
        logger.error("Error: current guest status is not shutoff or shutdown,\
                      can not do restore operation")
        return return_close(conn, logger, 1)

    try:
        conn.restore(filepath)
        if check_guest_restore(guestname, domobj, util, logger):
            logger.info("restore %s domain successful" % guestname)
            test_result = True
        else:
            logger.error("Error: fail to check restore domain")
            test_result = False
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("Error: fail to restore %s domain" % guestname)
        test_result = False

    if test_result:
        return return_close(conn, logger, 0)
    else:
        return return_close(conn, logger, 1)

def restore_clean(params):
    """ clean the testing environment """
    pass
