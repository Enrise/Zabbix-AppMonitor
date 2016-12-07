#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Application Monitoring v2
"""
import argparse
import socket
import sys
import protobix
import requests

class AAMv2(protobix.SampleProbe):
    __version__="2.0.0"
    severities = ['unclassified','information','warning','average','high','disaster']

    def _validate_severity(self, severity):
        return severity in self.severities

    def _get_severity(self, component):
        return 'unclassified' if not isinstance(component, dict) \
                or not 'severity' in component \
                or not self._validate_severity(component['severity']) else component['severity']

        return severity

    def _get_timeout(self):
        try:
            with open('/etc/zabbix/zabbix_server.conf') as myfile:
                for line in myfile:
                    name, var = line.partition("=")[::2]
                    if name == "Timeout":
                        return float(var.strip()) - 2.0
        except:
            pass

        # Failsafe return in case we cannot deal with the file / cannot find the timeout key
        if self.logger:  # pragma: no cover
            self.logger.info('Timeout setting not found, defaulting to 28.0')
        return float(28.0)

    def _get_content(self):
        content = False

        timeout = self._get_timeout()

        headers = {
            'User-Agent': 'AAMv2/{0}'.format(self.__version__),
        }

        try:
            content = requests.get(self.options.url, headers=headers, timeout=timeout).json()
        except requests.exceptions.Timeout:
            if self.logger:
                self.logger.error('HTTP timeout while retrieving content for {0} after {1} seconds.'.format(self.options.hostname, timeout,))
        except requests.exceptions.RequestException as e:  # catastrophic error. bail.
            if self.logger:  # pragma: no cover
                self.logger.error('HTTP error occurred while retrieving content for {0}: {1}'.format(self.options.hostname, e,))

        return content

    def _parse_probe_args(self, parser):
        # Parse the script arguments
        # parser is an instance of argparse.parser created by SampleProbe._parse_args method
        # you *must* return parser to SampleProbe so that your own options are taken into account
        probe_options = parser.add_argument_group('AAMv2 configuration')
        probe_options.add_argument('hostname', help='Hostname as known in Zabbix')
        probe_options.add_argument('url', help='JSON Feed to retrieve information from')

        return parser

    def _init_probe(self):
        # Whatever you need to initiliaze your probe
        # Can be establishing a connection
        # Or reading a configuration file
        # If you have nothing special to do
        # Just do not override this method
        # Or use:
        pass

    def _get_discovery(self):
        # Whatever you need to do to discover LLD items
        # this method is mandatory
        # If not declared, calling the probe ith --discovery option will resut in a NotimplementedError
        components = self._get_content()
        if not components:
            if self.logger:
                self.logger.error('Unable to retrieve discovery for host {0}.'.format(self.options.hostname))

            return False

        data = {}
        discovery_data = {}

        for component in components:
            try:
                severity = self._get_severity(components[component])

                discoveryKey = 'aamv2.discovery[{0}]'.format(severity)
                discovery_data.setdefault(discoveryKey, list())

                discovery_data[discoveryKey].append({'{#COMPONENT}': component, '{#SEVERITY}': severity})
            except:
                pass

        try:
            data[self.options.hostname] = discovery_data
        except:
            return data

        return data


    def _get_metrics(self):
        # Whatever you need to do to collect metrics
        # this method is mandatory
        # If not declared, calling the probe with --update-items option will resut in a NotimplementedError
        components = self._get_content()

        if not components:
            if self.logger:
                self.logger.error('Unable to retrieve status for host {0}.'.format(self.options.hostname))
            return False

        data = {self.options.hostname: {}}

        for component in components:
            try:
                severity = self._get_severity(components[component])

                item_key = 'aamv2.status["{0}",{1}]'.format(component,severity)
                data[self.options.hostname][item_key] = components[component]['statusCode']
            except:
                pass

        return data

if __name__ == '__main__':
    ret = AAMv2().run()
    print ret
    sys.exit(ret)
