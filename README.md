# NAME

SSHOPE.py - SSH automation tool


## Overview

A python script inspired by Infrastracutre as code, a push-type configuration management tool.
The tool is just a tool to execute the command to the destination of the ssh connection according to the definition of yaml, specifying a configuration file (yaml file) as the argument of this tool.

## Prerequisite

This tool has been tested on Windows, Linux and macOS where python is installed.
Linux and UNIX servers with SSH connection.

* python 3.7+
* python library(pyyaml,paramiko,scp)
* macOS 10.14+ or Windows10+ or Linux7+

## Usage

    $ python SSHOPE.py xxxx.yaml


xxxx is optional.


## How to Write a YAML File (Configuration Definition)

---
  - hostname: 		      hostname or IP  You can specify more than one by comma.
  - port: xx                  The port number to connect to.
  - userid: xxxx              User ID to connect to.
  - passwd: xxxx
  - keyfile: xxxx.pem         Optional. If a keyfile is specified, passwd cannot be listed.
  - ope: OS command1
  - ope: OS command2
---

## Note

1) Each command described in Operation about the yaml to be read should use a command that can guarantee idempotence. Override options and such.

2) If you want to use scp for operation in yaml, use scp@"put or get"@copy source@copy destination. The delimiter is "@".

3) Environment variables （\_${XXX}) in yaml can be replaced with environment variables set to the OS. If you want to replace it, you need to set the OS environment variables in advance. The yaml environment variable $\_{HOGE} should be set in advance like $env:HOGE="AAA" in powershell or set HOGE="AAA" in DOS, so that you don't have to write passwd and so one
XXX in \_${XXX} should be the letters in a-zA-Z0-9. Special characters and 2-byte characters are not allowed.

4) When inserting a password into the environment variable (\_${XXX}) in yaml, be sure to use the format $\_{~PASSWD}.

5) The error handling of YAML's OPE is looking at the standard error output. If you want to stop the process in the middle, output the standard error. Note that I have not seen the return code. If you want to continue the process, add 2>&1 at the end of the command, or put ERREXCEPTLIST.conf at the same level as SSHOPE.py and define an inline error output message (partial matching is possible).

## Licence

SSHOPE.py is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).


