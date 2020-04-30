#!/bin/bash

  if [ $# -ne 1 ];then
      echo "./本シェル [プロキシアドレス:プロキシポート]"
      exit 255
  fi

  PROXY=$1

  # node_exporter起動確認
  ps -ef | grep node_exporter | grep -v grep
  if [ $? -eq 0 ]; then 
      echo 'すでにnode_exporterが起動しています'
      exit 255
  fi

  # prometheus用のメトリクス取得ツール（NodeExporter）のダウンロード，起動
  curl -x ${PROXY} -LO https://github.com/prometheus/node_exporter/releases/download/v0.18.0/node_exporter-0.18.0.linux-amd64.tar.gz 2>&1
  tar xvzf ~/node_exporter-0.18.0.linux-amd64.tar.gz
  rm -rf ~/node_exporter-0.18.0.linux-amd64.tar.gz

  # node_exporterサービス起動定義ファイル生成
  if [ ! -f /etc/systemd/system/node_exporter.service ];then
       sudo cat > /etc/systemd/system/node_exporter.service <<EOF 
[Unit]
Description = node_exporter

[Service]
ExecStart = /home/ubuntu/node_exporter-0.18.0.linux-amd64/node_exporter 
Restart = always
Type = simple

[Install]
WantedBy = multi-user.target
EOF
  fi

  # サービスが登録されたかチェック
  sudo systemctl list-unit-files --type=service | grep node_exporter 
  if [ $? -ne 0 ];then
     echo "node_exporterのサービス登録に失敗しました"
     exit 255
  fi

  sudo systemctl enable node_exporter
  sudo systemctl start node_exporter
