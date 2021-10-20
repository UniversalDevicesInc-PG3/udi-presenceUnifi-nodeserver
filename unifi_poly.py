#!/usr/bin/env python3

"""
This is a NodeServer for Unifi Device Detection written by automationgeek (Jean-Francois Tremblay)
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com
"""
import udi_interface
import hashlib
import warnings 
import time
import json
import sys
from copy import deepcopy
from urllib.parse import quote
from pushover import init, Client
from unifi_api_controller import Controller as unifictl

LOGGER = udi_interface.LOGGER
SERVERDATA = json.load(open('server.json'))
VERSION = SERVERDATA['credits'][0]['version']

def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    f.close()
    return { 'version': pv }

class Controller(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'UnifiCtrl'
        self.queryON = False
        self.hb = 0
        self.unifi_host = ""
        self.unifi_port = ""
        self.unifi_userid = "" 
        self.unifi_password = ""
        self.unifi_siteid = ""
        self.mac_device = ""
        self.poToken = ""
        self.poUserKey = ""
        self.lstUsers = []
        self.ctrl = None

        polyglot.subscribe(polyglot.START, self.start, address)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.parameterHandler)
        polyglot.subscribe(polyglot.POLL, self.poll)

        polyglot.ready()
        polyglot.addNode(self)

    def parameterHandler(self, params):
        self.poly.Notices.clear()
        try:
            if 'unifi_host' in params:
                self.unifi_host = params['unifi_host']
            else:
                self.unifi_host = ""
                
            if 'unifi_port' in params:
                self.unifi_port = params['unifi_port']
            else:
                self.unifi_port = "8443"    
            
            if 'unifi_userid' in params:
                self.unifi_userid = params['unifi_userid']
            else:
                self.unifi_userid = ""
            
            if 'unifi_password' in params:
                self.unifi_password = params['unifi_password']
            else:
                self.unifi_password = ""
            
            if 'unifi_siteid' in params:
                self.unifi_siteid = params['unifi_siteid']
            else:
                self.unifi_siteid = "default"              
            
            if 'poToken' in params:
                self.poToken = params['poToken']
            else:
                self.poToken = ""

            if 'poUserKey' in params:
                self.poUserKey = params['poUserKey']
            else:
                self.poUserKey = ""
      
            if 'mac_device' in params:
                self.mac_device = params['mac_device']
            else:
                self.mac_device = ""      
          
            if self.unifi_host == "" or self.unifi_userid == "" or self.unifi_password == "" or self.mac_device == "" :
                self.poly.Notices['cfg'] = 'Unifi requires \'unifi_host\' \'unifi_userid\' \'unifi_password\' \'mac_device\' parameters to be specified.'
                LOGGER.error('Unifi requires \'unifi_host\' \'unifi_userid\' \'unifi_password\' \'mac_device\' parameters to be specified in custom configuration.')
                return False
            else:
                self.discover()
                
        except Exception as ex:
            LOGGER.error('Error starting Unifi NodeServer: %s', str(ex))

    def start(self):
        LOGGER.info('Started Unifi for v3 NodeServer version %s', str(VERSION))
        self.setDriver('ST', 0)
           
    def poll(self, polltype):
        if 'shortPoll' in polltype:
            self.setDriver('ST', 1)
            for node in self.poly.nodes():
                if  node.queryON == True :
                    node.update()
        else:
            #self._newUsers()
            self.heartbeat()
        
    def query(self):
        for node in self.poly.nodes():
            node.reportDrivers()

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def discover(self, *args, **kwargs):
        
        self.ctrl = unifictl(self.unifi_host,self.unifi_userid,self.unifi_password,self.unifi_port,site_id=self.unifi_siteid,ssl_verify=False)
        
        #for user in self.ctrl.get_users() :
        #    self.lstUsers.append(user["mac"])
            
        for netdevice in self.mac_device.split(','):
            name =  netdevice.replace(":","") 
            if not self.poly.getNode(name):
                self.poly.addNode(NetDevice(self.poly,self.address,name,name,self.ctrl,netdevice ))

    def delete(self):
        LOGGER.info('Deleting Unifi')

    def _newUsers(self):
        lstCurUsers = []
        for user in self.ctrl.get_users() :
            lstCurUsers.append(user["mac"])

        lstNewUserFound = list(set(self.lstUsers) - set(lstCurUsers))

        if ( len(lstNewUserFound) ) :
            self._sentPushOver(''.join(lstNewUserFound))
            LOGGER.info("New users found :" + ' '.join(lstNewUserFound) )
            self.lstUser = lstCurUsers.copy()
        else:
             LOGGER.info("No new users found")

    def _sentPushOver(self,message):
        init(self.poToken)
        Client(self.poUserKey).send_message(message, title="UniFi new users found")
        
    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]

class NetDevice(udi_interface.Node):

    def __init__(self, controller, primary, address, name,ctrl, mac):

        super(NetDevice, self).__init__(controller, primary, address, name)
        self.queryON = True
        self.deviceMac = mac
        self.unifiCtrl = ctrl

        controller.subscribe(controller.START, self.start, address)

    def start(self):
        self.update()

    def query(self):
        self.reportDrivers()
        
    def update(self):
        try :
            if ( 'essid' in self.unifiCtrl.get_client(self.deviceMac) ) :
                self.setDriver('GV1',1)
            else:
                self.setDriver('GV1',0)
            
        except Exception as ex :
            self.setDriver('GV1',0)
            LOGGER.info('update: %s', str(ex))
            
    drivers = [{'driver': 'GV1', 'value': 0, 'uom': 2}]

    id = 'UNIFI_DEVICE'
    commands = {
                }

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start()
        polyglot.updateProfile()
        polyglot.setCustomParamsDoc()
        Controller(polyglot, 'controller', 'controller', 'UnifiNodeServer')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
