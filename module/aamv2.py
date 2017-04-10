#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Application Monitoring v2
"""
import sys

import protobix
import requests


class AAMv2(protobix.SampleProbe):
    __version__ = "2.0.1"
    severities = ['unclassified', 'information', 'warning', 'average', 'high', 'disaster']

    def _validate_severity(self, severity):
        return severity in self.severities

    def _get_severity(self, component):
        if isinstance(component, unicode) \
                or isinstance(component, str) \
                or not isinstance(component, dict) \
                or not 'severity' in component \
                or not self._validate_severity(component['severity']):
            return 'unclassified'
        else:
            return component['severity']

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
                self.logger.error(
                    'HTTP timeout while retrieving content for {0} after {1} seconds.'.format(self.options.hostname,
                                                                                              timeout, ))
        except requests.exceptions.RequestException as e:  # catastrophic error. bail.
            if self.logger:  # pragma: no cover
                self.logger.error(
                    'HTTP error occurred while retrieving content for {0}: {1}'.format(self.options.hostname, e, ))

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
        # Whatever you need to initialize your probe
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

        if isinstance(components, list):
            if self.logger:
                self.logger.debug(
                    'Upgrading response to v2 compatible format for host {0}.'.format(self.options.hostname))
                components = self._upgrade_v1_discovery_response(components)

        data = {}
        discovery_data = {}

        for component in components:
            try:
                severity = self._get_severity(components[component])

                discoveryKey = 'aamv2.discovery[{0}]'.format(severity)
                discovery_data.setdefault(discoveryKey, list())

                discovery_data[discoveryKey].append({'{#COMPONENT}': component, '{#SEVERITY}': severity})
            except:
                if self.logger:  # pragma: no cover
                    self.logger.error('Unable to retrieve components for host {0}.'.format(self.options.hostname))

                pass

        try:
            data[self.options.hostname] = discovery_data
        except:
            pass

        return data

    def _upgrade_v1_discovery_response(self, components):
        dct = {}
        for component in components:
            dct[component] = {'severity': 'disaster'}
        return dct

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
                if 'severity' not in components[component]:
                    # Become bw compatible with v1 endpoints where severity is not part of the return dict
                    if self.logger:
                        self.logger.debug(
                            'Upgrading response to v2 compatible format for host {0}.'.format(self.options.hostname))
                    components[component]['severity'] = 'disaster'

                severity = self._get_severity(components[component])

                item_key = 'aamv2.status["{0}",{1}]'.format(component, severity)
                data[self.options.hostname][item_key] = components[component]['statusCode']
            except:
                if self.logger:  # pragma: no cover
                    self.logger.error('Unable to retrieve metrics for host {0}.'.format(self.options.hostname))
                pass

        return data


if __name__ == '__main__':
    ret = AAMv2().run()
    print ret
    sys.exit(ret)
