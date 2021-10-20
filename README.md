# UniFi Device Network Presence Detection Polyglot V3 Node Server

![Build Status](https://travis-ci.org/therealmysteryman/udi-presenceUnifi-nodeserver.svg?branch=master)

This nodeserver provides an interface between Unifi Controller and Polyglot v2 server. This nodesever stricly detect if a device is present on your network or not.

## Installation

1. Install from Polyglot store :
2. Add following custom configurations :
    - unifi_host -> UDM / Cloud Key - IP
    - unifi_port -> UDM / Cloud Key - Port
    - unifi_userid -> UDM / Cloud Key - UserID
    - unifi_password -> UDM / Cloud Key - Password
    - unifi_siteid -> UDM / Cloud Key - Site (default)
    - mac_device -> Provide a comma delimited list of mac address of device to detect presence on the network. (ff:ff:ff:ff:ff:ff,ff:ff:ff:ff:ff:ff)

## Source

1. Using this Python Library to control the Unifi - https://github.com/NickWaterton/Unifi-websocket-interface/blob/master/controller.py
2. Based on the Node Server Template - https://github.com/Einstein42/udi-poly-template-python
