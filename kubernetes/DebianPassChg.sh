#!/bin/bash
# 注意 expectがインストールされていなければyum install expectでインストール。
# Debian sudo版

if [ $# -ne 2 ];then
   echo "./本シェル [対象ID] [新パスワード]"
   exit 255
fi

TARGETID=$1
NEWPASS=$2
# Redhat系
#PASSWDPROMPT=".*${TARGETID}.\nNew password:"
# Debian系
PASSWDPROMPT=".*password:"
PASSWDPROMPTONEMORE=".*password:"
LANG=ja_JP.UTF-8;export LANG

expect -c "
set timeout 10
spawn sudo passwd ${TARGETID}
expect -re \"${PASSWDPROMPT}\"
send -- \"${NEWPASS}\n\"
expect -re \"${PASSWDPROMPTONEMORE}\"
send -- \"${NEWPASS}\n\"
expect -re \"\.*successfully\n.*$\"
exit 0
"
