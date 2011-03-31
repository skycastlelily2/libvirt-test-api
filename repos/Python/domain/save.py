#!/usr/bin/env python
"""this test case is used for testing
   save domain to disk file
   mandatory arguments: guestname
                        filepath
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue Mar 23, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'get_guest_ipaddr', 'check_guest_status',
           'check_guest_save', 'save']

import os
import re
import sys

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib.Python import connectAPI
from lib.Python import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'filepath' ]
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def get_guest_ipaddr(*args):
    """Get guest ip address"""
    (guestname, util, logger) = args

    mac = util.get_dom_mac_addr(guestname)
    logger.debug("guest mac address: %s" %mac)

    ipaddr = util.mac_to_ip(mac, 15)
    logger.debug("guest ip address: %s" %ipaddr)

    if util.do_ping(ipaddr, 20) == 1:
        logger.info("ping current guest successfull")
        return ipaddr
    else:
        logger.error("Error: can't ping current guest")
        return None

def check_guest_status(*args):
    """Check guest current status"""
    (guestname, domobj, logger) = args

    state = domobj.get_state(guestname)
    logger.debug("current guest status: %s" %state)

    if state == "shutoff" or state == "shutdown" or state == "blocked":
        return False
    else:
        return True

def check_guest_save(*args):
    """Check save domain result, if save domain is successful,
       guestname.save will exist under /tmp directory and guest
       can't be ping and status is paused
    """
    (guestname, domobj, util, logger) = args

    if not check_guest_status(guestname, domobj, logger):
        if not get_guest_ipaddr(guestname, util, logger):
            return True
        else:
            return False
    else:
        return False

def save(params):
    """Save domain to a disk file"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    filepath = params['filepath']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Save domain
    domobj = domainAPI.DomainAPI(virconn)
    ipaddr = get_guest_ipaddr(guestname, util, logger)

    if not check_guest_status(guestname, domobj, logger):
        logger.error("Error: current guest status is shutoff")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    if not ipaddr:
        logger.error("Error: can't get guest ip address")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
    try:
        domobj.save(guestname, filepath)
        if check_guest_save(guestname, domobj, util, logger):
            logger.info("save %s domain successful" %guestname)
            test_result = True
        else:
            logger.error("Error: fail to check save domain")
            test_result = False
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to save %s domain" %guestname)
        test_result = False
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1

