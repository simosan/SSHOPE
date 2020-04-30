#!/bin/bash

  if [ $# -ne 1 ];then
      echo "./本シェル [プロキシアドレス:プロキシポート]"
      exit 255
  fi

  PROXY=$1
  MASTERNODEIP=`ip a | grep 'en\|eth0' | grep "inet" | cut -d' ' -f6 | cut -d/ -f1`
  # PROXY
  export HTTP_PROXY=$PROXY
  export HTTPS_PROXY=$PROXY
  # podに割り当てられる10.96.0.0/12とFlannelのオーバレイＮＷアドレス10.244.0.0/16は除外しておく
  export NO_PROXY=localhost,127.0.0.1,10.96.0.0/12,10.244.0.0/16,$MASTERNODEIP


  # apt-get stdin Error対応
  export DEBIAN_FRONTEND=noninteractive
  # ホスト名を変数に格納
  HOSTNAME=$(hostname -s) 
  # kubeadm initの実行
  # Flannelの場合cidrは10.244.0.0/16縛り
  #kubeadm init --node-name $HOSTNAME --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=$MASTERNODEIP
  IPADDR=$(ip a | grep 'en\|eth0' | grep "inet" | cut -d' ' -f6 | cut -d/ -f1)
  kubeadm init --apiserver-advertise-address=$IPADDR --apiserver-cert-extra-sans=$IPADDR --node-name $HOSTNAME --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12
  # ubuntuユーザーがkubectlを実行できるようにする
  UBUHOME=/home/ubuntu
  sudo --user=ubuntu mkdir -p $UBUHOME/.kube
  cp -i /etc/kubernetes/admin.conf $UBUHOME/.kube/config
  chown $(id -u ubuntu):$(id -g ubuntu) $UBUHOME/.kube/config
  # Flannelのインストール
  export KUBECONFIG=/etc/kubernetes/admin.conf
  curl -x $PROXY -o $UBUHOME/kube-flannel.yml https://raw.githubusercontent.com/coreos/flannel/bc79dd1505b0c8681ece4de4c0d86c5cd2643275/Documentation/kube-flannel.yml
  kubectl apply -f $UBUHOME/kube-flannel.yml
  # kubectl joinコマンドを保存する
  kubeadm token create --print-join-command > /etc/kubeadm_join_cmd.sh
  sudo chmod +x /etc/kubeadm_join_cmd.sh
  # 他ノードからscpゲットできるようにホームディレクトリにコピーする
  sudo cp -p /etc/kubeadm_join_cmd.sh $UBUHOME/
  sudo chown $(id -u ubuntu):$(id -g ubuntu) kubeadm_join_cmd.sh

  # helm（kubernetesパッケージマネージャ）
  VERSION="v2.13.1" # kuberketes 1.14
  curl -x $PROXY -LO https://storage.googleapis.com/kubernetes-helm/helm-${VERSION}-linux-amd64.tar.gz
  tar zxvf helm-${VERSION}-linux-amd64.tar.gz
  cp linux-amd64/helm /usr/local/bin/
  rm -rf linux-amd64
  rm -f helm-${VERSION}-linux-amd64.tar.gz
  # git
  sudo apt-get install -y git 2>&1
  git config --global http.proxy http://$PROXY
  git config --global https.proxy http://$PROXY
  # kubens/kubectx（クラスタ切り替え,namespace切り替えツール）
  git clone https://github.com/ahmetb/kubectx.git /opt/kubectx
  ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx
  ln -s /opt/kubectx/kubens /usr/local/bin/kubens
  # kube-ps1
  git clone https://github.com/jonmosco/kube-ps1.git /opt/kube-ps1
  grep "kube-ps1.sh" $UBUHOME/.bashrc
  if [ $? -eq 1 ];then
     cat <<'EOF' >> $UBUHOME/.bashrc
source /opt/kube-ps1/kube-ps1.sh
KUBE_PS1_SUFFIX=') '
PS1='$(kube_ps1)'$PS1
EOF
  fi
  # prometheous
  docker pull prom/prometheus
  # grafana
  docker pull grafana/grafana

  # kubectlの補完を有効にする
  echo "source <(kubectl completion bash)" >> $UBUHOME/.bashrc 