#!/bin/bash

  if [ $# -ne 2 ];then
      echo "./本シェル [プロキシアドレス:プロキシポート] [マスターノードIP]"
      exit 255
  fi

  #PROXY=$1
  #MASTERIP=$2
  # PROXY
  #export HTTP_PROXY=$PROXY
  #export HTTPS_PROXY=$PROXY
  # podに割り当てられる10.96.0.0/12とFlannelのオーバレイＮＷアドレス10.244.0.0/16は除外しておく
  #export NO_PROXY=localhost,127.0.0.1,10.96.0.0/12,10.244.0.0/16,$MASTERIP

  # kubernetesクラスタにjoin
  sudo sh ./kubeadm_join_cmd.sh 2>&1