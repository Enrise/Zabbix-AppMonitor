#!/usr/bin/env python
"""
Advanced Application Monitoring
"""
import sys
import requests
import argparse

import protobix


class AAM(object):
    __version__ = '0.0.1'
    ZBX_CONN_ERR = 'ERR - unable to send data to Zabbix [%s]'

    def _init_container(self):
        zbx_container = protobix.DataContainer(
            data_type='items',
            zbx_host='localhost'
        )
        return zbx_container

    def _get_discovery(self, hostname, url):
        components = requests.get(url).json()

        if not components:
            return False

        data = {}

        discovery_key = 'aam.discovery'
        discovery_data = {discovery_key: []}

        for component in components:
            try:
                discovery_data[discovery_key].append({'{#COMPONENT}': component})
            except:
                pass

        try:
            data[hostname] = discovery_data
        except:
            return False

        return data

    def _get_status(self, hostname, url):
        components = requests.get(url).json()
        if not components:
            return False

        data = {hostname: {}}

        for component in components:
            try:
                item_key = 'aam.status[{0}]'.format(component)
                data[hostname][item_key] = components[component]['statusCode']
            except:
                pass

        return data

    def run(self):
        parser = argparse.ArgumentParser(description='Automatic Application Monitoring')
        parser.add_argument('task', choices=['discovery', 'status'], help='Task to execute')
        parser.add_argument('hostname', help='Hostname as known in Zabbix')
        parser.add_argument('url', help='JSON Feed to retrieve information from')

        args = parser.parse_args()

        try:
            zbx_container = self._init_container()
        except:
            return 1

        if args.task == 'discovery':
            zbx_container.set_type("lld")
            data = self._get_discovery(args.hostname, args.url)
        elif args.task == 'status':
            data = self._get_status(args.hostname, args.url)

        if not data:
            return 3

        try:
            zbx_container.add(data)
        except:
            return 4

        try:
            zbx_container.send()
        except:
            return 5

        # Everything went fine. Let's return 0 and exit
        return 0


if __name__ == '__main__':
    ret = AAM().run()
    print ret
    sys.exit(ret)
