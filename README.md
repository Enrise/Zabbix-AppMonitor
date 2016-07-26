Automatic Application Monitoring
===
This Zabbix "module" provides automated Application Component monitoring by utilizing the Low-Level Discovery functionality of Zabbix.

It automatically creates items and triggers based on a list of components provided by the application.

Background details: https://enrise.com/2015/10/automating-application-component-monitoring/

## Requirements for your application
In your application you should create two endpoints which should be available as a page which responds with JSON.

### Key endpoint
This should return a JSON array of available keys like so:
```json
["api",
"filesystem",
"mysql",
"redis",
"rabbitmq",
"vpn",
"backup"
]
```

### Status endpoint
This should return the status in JSON for all available components:
```json
{
  "api":{"statusCode":2,"status":"Degraded"},
  "filesystem":{"statusCode":2,"status":"Degraded"},
  "mysql":{"statusCode":2,"status":"Degraded"},
  "redis":{"statusCode":2,"status":"Degraded"},
  "rabbitmq":{"statusCode":2,"status":"Degraded"},
  "vpn":{"statusCode":1,"status":"Failure"},
  "backup":{"statusCode":0,"status":"OK"}
}
```

The field "status" is currently not being used, only "statusCode".

## Installation in Zabbix

* Install the dependencies for AAM:
```shell
$ sudo pip install -r requirements.txt
```
If pip is not present on your system:
```shell
$ sudo easy_install pip
```

* Add `aam.py` to your external scripts (default: `/usr/lib/zabbix/externalscripts/`) folder on your Zabbix Server and ensure it is executable.

* Under `Configuration => Templates` in the Zabbix webinterface import `zbx_aam_template.xml`
* To the host you want to monitor, add the following macro's:

| Macro                  | Value                                 |
|------------------------|---------------------------------------|
| {$AAM_KEY_ENDPOINT}    | http://your-application/appmon/keys   |
| {$AAM_STATUS_ENDPOINT} | http://your-application/appmon/status |

*The URL's should point towards the endpoints you have created. They can be routes, individual pages, static files or queryable with HTTP-Parameters depending on your application as long as the output matches what the module requires.*

* Optionally you can override the default values for some querying periods:

| Macro                      | Default value  |
|----------------------------|----------------|
| $AAM_THRESHOLD_COMPONENT   |       5m       |
| {$AAM_THRESHOLD_KEY}       |       #2       |
| {$AAM_THRESHOLD_STATUS}    |       #2       |

* Assign the template `Template Automatic Application Monitoring` to the host you want to monitor the application of. If your host has multiple applications its recommended to create a dummy host in Zabbix for each application on the server.
* After some time it will automatically create the items and trigger for status reporting

## Demo app
The folder `demoapp` contains a [Lumen](http://lumen.laravel.com/) PHP application which showcases the output it can generate. The most interesting part of the code is the `app/Http/Controllers/StatusController.php`.

This app serves as a demo on how to implement it. It is in no way a requirement to be able to use the Zabbix module.

## Contributing
Contributions to this module and its implementation are welcome!

### License
The MIT License (MIT). Please see the [license file](LICENSE) for more information.
