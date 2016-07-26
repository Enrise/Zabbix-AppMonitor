#!/usr/bin/env python
"""
Advanced Application Monitoring
"""
import sys
import requests
import argparse
import syslog
import protobix


class AAM(object):
    __version__ = '0.1'

    def _init_container(self):
        zbx_container = protobix.DataContainer(
            data_type='items',
            zbx_host='localhost'
        )
        return zbx_container

    def _get_timeout(self):
        with open('/etc/zabbix/zabbix_server.conf') as myfile:
            for line in myfile:
                name, var = line.partition("=")[::2]
                if name == "Timeout":
                    return float(var.strip()) - 2.0

        # Failsafe return in case we cannot deal with the file / cannot find the timeout key
        syslog.syslog(syslog.LOG_INFO, 'Timeout setting not found, defaulting to 28.0')
        return float(28.0)

    def _get_content(self, hostname, url):
        content = False

        timeout = self._get_timeout()
        try:
            content = requests.get(url, timeout=timeout).json()
        except requests.exceptions.Timeout:
            syslog.syslog(syslog.LOG_ERR,
                          '[%s] HTTP timeout while retrieving content after %d seconds.' % (hostname, timeout,))
        except requests.exceptions.RequestException as e:  # catastrophic error. bail.
            syslog.syslog(syslog.LOG_ERR, '[%s] HTTP error occurred while retrieving content: %s' % (hostname, e,))

        return content

    def _get_discovery(self, hostname, url):
        components = self._get_content(hostname, url)

        if not components:
            syslog.syslog(syslog.LOG_ERR, '[%s] Unable to retrieve discovery for host.' % (hostname))
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
        components = self._get_content(hostname, url)

        if not components:
            syslog.syslog(syslog.LOG_ERR, '[%s] Unable to retrieve status for host.' % (hostname))
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
        data = False

        parser = argparse.ArgumentParser(description='Automatic Application Monitoring')
        parser.add_argument('task', choices=['discovery', 'status'], help='Task to execute')
        parser.add_argument('hostname', help='Hostname as known in Zabbix')
        parser.add_argument('url', help='JSON Feed to retrieve information from')

        args = parser.parse_args()

        try:
            zbx_container = self._init_container()
        except:
            syslog.syslog(syslog.LOG_ERR, '[%s] Error while initializing container' % args.hostname)
            return 1

        if args.task == 'discovery':
            zbx_container.set_type("lld")
            data = self._get_discovery(args.hostname, args.url)
        elif args.task == 'status':
            data = self._get_status(args.hostname, args.url)

        if not data:
            syslog.syslog(syslog.LOG_ERR, '[%s] No %s data returned ' % (args.hostname, args.task,))
            return 3

        try:
            zbx_container.add(data)
        except:
            syslog.syslog(syslog.LOG_ERR, '[%s] Error while adding data to container' % args.hostname)
            return 4

        try:
            zbx_container.send()
        except:
            syslog.syslog(syslog.LOG_ERR, '[%s] Error while sending data to Zabbix' % args.hostname)
            return 5

        # Everything went fine. Let's return 0 and exit
        return 0


if __name__ == '__main__':
    ret = AAM().run()
    print(ret)
    sys.exit(ret)
