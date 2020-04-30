#!/bin/bash

  if [ $# -ne 1 ];then
      echo "./本シェル [プロキシアドレス:プロキシポート]"
      exit 255
  fi

  PROXY=$1

  # PROXY
  export HTTP_PROXY=$PROXY
  export HTTPS_PROXY=$PROXY
  # podに割り当てられる10.96.0.0/12とFlannelのオーバレイＮＷアドレス10.244.0.0/16は除外しておく
  export NO_PROXY=localhost,127.0.0.1,10.96.0.0/12,10.244.0.0/16

  # bashrcにプロキシ環境変数を設定しておく
  grep "HTTP_PROXY" ~/.bashrc
  if [ $? -eq 1 ];then
       cat <<EOF >> ~/.bashrc
export HTTP_PROXY=$PROXY
export HTTPS_PROXY=$PROXY
export NO_PROXY=localhost,127.0.0.1,10.96.0.0/12,10.244.0.0/16
EOF
  fi
  source ~/.bashrc

  # apt-get stdin Error対応
  export DEBIAN_FRONTEND=noninteractive
  # パッケージ公開鍵更新
  sudo apt-key adv --keyserver keyserver.ubuntu.com --keyserver-option http-proxy=http://$PROXY --recv-keys 6A030B21BA07F4FB
  # パッケージ更新
  sudo apt-get update 2>&1
  # Dockerの前提パッケージ
  sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common 2>&1
  # Dockerのレポジトリ追加
  curl -x $PROXY -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  # Dockerのインストール(とりあえず18.06)
  sudo apt-get update 2>&1
  sudo apt-get install -y docker-ce=$(apt-cache madison docker-ce | grep 18.06 | head -1 | awk '{print $3}') 2>&1
  sudo apt-mark hold docker-ce
  # Dockerデーモンの設定
  if [ ! -e "/etc/docker/daemon.json" ];then
      sudo cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
  fi

  sudo mkdir -p /etc/systemd/system/docker.service.d

  # Dockerプロキシ設定
  if [ ! -e "/etc/systemd/system/docker.service.d/http-proxy.conf" ];then
     sudo cat > /etc/systemd/system/docker.service.d/http-proxy.conf <<EOF
[Service]
Environment="HTTP_PROXY=http://$PROXY/" "HTTPS_PROXY=http://$PROXY/" "NO_PROXY=localhost,127.0.0.1"
EOF
  fi
  sudo systemctl daemon-reload
  sudo systemctl restart docker

  # ubuntuユーザーをdockerグループに追加
  sudo usermod -aG docker ubuntu

  # Flannelの場合に必要
  # 各ノードで動作するpodのブリッジ通信をiptableが邪魔するので無効化
  grep "net.bridge.bridge-nf-call-iptables" /etc/sysctl.conf
  if [ $? -eq 1 ];then
      sudo bash -c "echo net.bridge.bridge-nf-call-iptables = 1 >> /etc/sysctl.conf"
      sudo sysctl -p
  fi

  # スワップを無効化する
  # スワップ領域がないのでコメントアウト
  swapoff -a
  # プロビジョニングで実行する場合はバックスラッシュのエスケープが必要なことに注意
  # sed -i '/ swap / s/^\\(.*\\)$/#\\1/g' /etc/fstab
  # nfsclient
  sudo apt-get install -y nfs-common 2>&1

  # Kubernetesのレポジトリ追加
  sudo curl -x $PROXY -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
  if [ ! -e "/etc/apt/sources.list.d/kubernetes.list" ];then
     sudo cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
  fi
  # kubeadm、kubelet、kubectlのインストール
  sudo apt-get update 2>&1
  # kubeadm、kubelet、kubectlのインストール（安定版1.14）
  VERSION=$(apt-cache madison kubeadm | grep 1.14 | head -1 | awk '{print $3}')
  sudo apt-get install -y kubelet=$VERSION kubeadm=$VERSION kubectl=$VERSION 2>&1
  sudo apt-mark hold kubelet kubeadm kubectl 2>&1
  # プライベートネットワークのNICのIPアドレスを変数に格納
  IPADDR=$(ip a | grep 'en\|eth0' | grep "inet" | cut -d' ' -f6 | cut -d/ -f1)
  echo "KUBELET_EXTRA_ARGS=--node-ip=$IPADDR" | sudo tee /etc/default/kubelet

  # kubeletを再起動
  sudo systemctl daemon-reload
  sudo systemctl restart kubelet
