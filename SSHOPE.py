#/*
#The MIT License (MIT)
#
#Copyright (c) 2020 m.simosan.
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.
#*/

# (動作要件)　pytnon3.7以降が導入されていること。pipでparamiko,pyyaml,scpをインストールしておくこと。
# (注意1)  本AP実行元はWindows,Linux,macOSに対応
# (注意2)  読み込ませるyamlについてOperationに記載する各コマンドは冪等性を担保できるコマンドを利用すること。上書きオプションとか
# (注意3)  yamlでOperetionにscpを使いたい場合は，scp@"put or get"@コピー元@コピー先とすること。区切り文字は"@"
# (注意4)  yaml内の環境変数(_${XXX})をOSに設定した環境変数に置換可能。置換したい場合はOSの環境変数を事前に設定しておくこと。
#          $_{HOGE}というyaml環境変数はpowershellでは$env:HOGE="AAA"，DOSではset HOGE="AAA"
#          といった具合に事前設定しておくと，passwd等をベタ書きにしなくてよい。
#          _${XXX}のXXXはa-zA-Z0-9内の文字にすること。特殊文字,2バイト文字はNG
# (注意5)  yamlに設定する環境変数(_${XXX})にパスワードを仕込む場合は，必ず，$_{~PASSWD}という形式にすること。
#          この形式に沿わないと，実行時コマンドの標準出力にパスワードが表示されてしまう（マスキングされない）。
# (注意6)  yamlのopeのエラーハンドリングは標準エラー出力でみている。途中で処理を停止したい場合は標準エラー出力をだすこと。
#          リターンコードは見ていないので注意すること。
#          標準エラー出力はでてしまうが，処理を継続したい場合はそのコマンド末尾に2>&1をいれるか，SSHOPE.pyと同一階層に
#          ERREXCEPTLIST.confを配置し，インラインでエラー出力メッセージ（部分一致可）を定義しておけば，処理が途中で
#          落ちることはない。
# (注意7)   hostnameに複数ホスト指定可能。カンマで区切る。
import paramiko
import sys
import yaml
import scp
import os
import re
import ctypes
import platform
from abc import ABCMeta, abstractmethod
from paramiko import SSHException


# ターミナルに出力するクラス（OSプラットフォーム判定処理を元に緑 or 赤処理を定義）


class Termout:

    # エラーメッセージ用
    @staticmethod
    def errmsgout(msg):
        _os = Termout.osplatform()
        if _os == 'Windows':
            objOs = WinColor()
            objOs.output_red(msg)
        elif _os == 'Linux' or _os == 'Darwin':
            objOs = UnixColor()
            objOs.output_red(msg)
        else:
            print("本APは" + _os + "をサポートしていません!!")
            sys.exit(255)

    # グリーンメッセージ用
    @staticmethod
    def greenmsgout(msg):
        _os = Termout.osplatform()
        if _os == 'Windows':
            objOs = WinColor()
            objOs.output_green(msg)
        elif _os == 'Linux' or _os == 'Darwin':
            objOs = UnixColor()
            objOs.output_green(msg)
        else:
            print("本APは" + _os + "をサポートしていません!!")
            sys.exit(255)

    # OS判定
    @staticmethod
    def osplatform():
        pf = platform.system()
        # Windowsの場合は"Windows”,Linuxの場合は"Linux",Macの場合は"Darwin"
        return pf


# OSプラットフォーム毎のターミナル 色付けクラス（ストラテジーパターン:抽象）
# Javaのインターフェースぽくしているので、本クラスを実装すると
# 以下抽象メソッド を全て実装しないとエラーがでます。


class AbstractColor(metaclass=ABCMeta):

    # 抽象メソッド（緑出力)
    @abstractmethod
    def output_green(self, msg):
        pass

    # 抽象メソッド （赤出力）
    @abstractmethod
    def output_red(self, msg):
        pass

# Windowsのターミナル 出力クラス(AbstraceColorを継承)


class WinColor(AbstractColor):

    def output_green(self, msg):
        # 色つけのためにWindows APIハンドルの設定いろいろ
        STD_OUTPUT_HANDLE = -11
        FOREGROUND_GREEN = 0x0002 | 0x0008  # 緑色/背景黒
        # ターミナル色付け用のハンドル取得
        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        reset = WinColor.get_csbi_attributes(handle)
        # メッセージを緑
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, FOREGROUND_GREEN)
        print(msg)
        # 色をもとに戻す
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, reset)

    def output_red(self, msg):
        # 色つけのためにWindows APIハンドルの設定いろいろ
        STD_OUTPUT_HANDLE = -11
        FOREGROUND_RED = 0x0004 | 0x0008  # 赤色/背景黒
        # ターミナル色付け用のハンドル取得
        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        reset = WinColor.get_csbi_attributes(handle)
        # エラーメッセージを赤
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, FOREGROUND_RED)
        print(msg)
        # 色をもとに戻す
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, reset)

    # ターミナルバッファクリア（色戻す）
    @staticmethod
    def get_csbi_attributes(handle):
        import struct
        csbi = ctypes.create_string_buffer(22)
        res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
        assert res

        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh",
                                                               csbi.raw)
        return wattr

# Linux Or Macのターミナル 出力クラス(AbscractColorを継承)


class UnixColor(AbstractColor):

    RED = '\033[31m'
    GREEN = '\033[32m'
    END = '\033[0m'

    def output_green(self, msg):
        print(self.GREEN + msg + self.END)

    def output_red(self, msg):
        print(self.RED + msg + self.END)


# 標準エラー出力エラーリスト格納オブジェクト


class ErrList:

    def __init__(self):
        # 本APと同一階層に標準エラー出力除外リスト（ERREXCEPTLIST.CONF）があれば読み込む
        try:
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "ERREXCEPTLIST.conf"),
                      encoding="utf-8") as efile:
                elist = [str.replace("\n", "") for str in list(efile)]
                self.__errlst = elist
        except FileNotFoundError:
            print("ERREXCEPTLIST.CONFが存在しないため除外処理は行いません")

    @property
    def errlst(self):
        return self.__errlst

    @errlst.setter
    def errlst(self, lst):
        self.__errlst = lst


# Linuxサーバへの接続用クラス
# yamlのTargetCon毎にインスタンスが生成される。


# 共通処理クラス


class CommonCls:

    # yamlの環境変数を展開(_${XXX}のXXXを展開)
    @staticmethod
    def envvarexpansion(var):
        # _${XXXXXX}はマスキングのため即リターン
        if var == '_${XXXXXX}':
            return var
        # 先頭が_$か本yamlの仕様どおり$_かチェック
        if var[0:2] == "_$":
            # 正規表現で環境変数文字列（_${XXX}）を抽出
            pattern = '_\${?(.*)}'
            result = re.match(pattern, var)
            if result:
                envstr = result.group(1)
                # OS環境変数を取得
                # import pdb; pdb.set_trace()
                try:
                    varrtn = os.environ[envstr]
                except KeyError:
                    Termout.errmsgout(var + "の値が設定されていません")
                    sys.exit(255)
            else:
                Termout.errmsgout("環境変数の設定ルールに誤りがあります（正：_${XXX})")
                sys.exit(255)
        else:
            Termout.errmsgout("環境変数の設定ルールに誤りがあります（正：_${XXX})")
            sys.exit(255)
        return varrtn

    # ope内の環境変数（_${XXX}）を値に置換
    @staticmethod
    def replacevar(opestr):
        # 正規表現で環境変数文字列（_${XXX}）を抽出
        pattern = '(_\${[a-zA-Z0-9]+})'
        result = re.findall(pattern, opestr)
        # マッチした環境変数のリストをenvvarexpansionで値取得
        # import pdb;pdb.set_trace()
        replaceopestr = opestr
        for i in result:
            tmpvar = CommonCls.envvarexpansion(i)
            replaceopestr = replaceopestr.replace(i, tmpvar)
        return replaceopestr

    # ope内のコマンドを標準出力（環境変数も展開）
    # ope内の環境変数にPASSWDが含まれていたら，XXXXXXでマスキングして標準出力
    @staticmethod
    def opeprint(opestr):
        # 正規表現で環境変数文字列にPASSWD(で終わる）が含まれているかを抽出(例)_${XXXPASSWD})
        patternpass = '.*_\$\{?(.*PASSWD)}'
        resultpass = re.findall(patternpass, opestr)
        replaceopepassstr = opestr
        # PASSWDが含まれていたらXXXXXXで置換
        for i in resultpass:
            replaceopepassstr = replaceopepassstr.replace(i, "XXXXXX")
        # 正規表現で環境変数文字列（_${XXX}）を抽出
        pattern = '(_\${[a-zA-Z0-9]+})'
        result = re.findall(pattern, replaceopepassstr)
        # マッチした環境変数のリストをenvvarexpansionで値取得
        replaceopestr = replaceopepassstr
        for i in result:
            tmpvar = CommonCls.envvarexpansion(i)
            replaceopestr = replaceopestr.replace(i, tmpvar)

        print(replaceopestr)


class SshCon:

    def __init__(self, hostdt, hstnm):
        # 初期化
        self.h = ""
        self.pt = ""
        self.u = ""
        self.p = ""
        self.rk = ""

        for idx in hostdt:
            for k, v in idx.items():
                if k == 'hostname':
                    self.h = hstnm
                elif k == 'port':
                    self.pt = v
                elif k == 'userid':
                    self.u = v
                elif k == 'passwd':
                    self.p = CommonCls.envvarexpansion(v)
                # 公開鍵認証の場合
                elif k == 'keyfile':
                    self.rk = v
        self.client = paramiko.SSHClient()
        # ssh接続が初めての場合は自動でknown_hostsに登録
        try:
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if len(self.p) != 0:
                self.client.connect(hostname=self.h,
                                    port=self.pt,
                                    username=self.u,
                                    password=self.p)
            elif len(self.rk) != 0:
                rsa_key = paramiko.RSAKey.from_private_key_file(self.rk)
                self.client.connect(hostname=self.h,
                                    port=self.pt,
                                    username=self.u,
                                    pkey=rsa_key)
        except SSHException as e:
            Termout.errmsgout('SSHException Connect Error!')
            Termout.errmsgout(str(e))
            self.client.close
            sys.exit(255)
        except TimeoutError as e:
            Termout.errmsgout('SSHException Connect Timeout Error!')
            Termout.errmsgout(str(e))
            self.client.close
            sys.exit(255)

    # TargetConのOperationを処理
    def sshserverope(self, oped):

        rtn = ''
        i = 1
        for idx in oped:
            # k=ope，v=操作
            # for~elseのelseはループが終了したら処理（上位のループに戻るという意味）
            # 当該ループでbreakが実行されたら，elseはスキップ。
            # つまり，エラーが発生したら，全ループから一気に抜ける。
            for k, v in idx.items():
                # import pdb; pdb.set_trace()
                # keyがope:じゃなかったらエラーでブレイク
                if k == "ope":
                    # ope内のコマンドを実際のコマンド文字列として表示（passwdはマスキング）
                    CommonCls.opeprint(v)
                    # ope内に環境変数があるかをチェック,あれば値に置換したopeに変更
                    v = CommonCls.replacevar(v)
                    # SCP操作なのかSSH操作なのかCheck
                    if v[:4] == 'scp@':
                        self.scpcmd(v)
                    else:
                        self.sshcmd(v)
                    i += 1
                    rtn = True
                else:
                    self.client.close
                    rtn = False
                    break
            else:
                continue
            break

        return rtn

    def scpcmd(self, cmdline):

        arrstr = cmdline.split('@') 
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # import pdb;pdb.set_trace()
            # パスワード認証 or 公開鍵認証
            if len(self.p) != 0:
                ssh.connect(hostname=self.h,
                            port=self.pt,
                            username=self.u,
                            password=self.p)
            elif len(self.rk) != 0:
                rsa_key = paramiko.RSAKey.from_private_key_file(self.rk)
                ssh.connect(hostname=self.h,
                            port=self.pt,
                            username=self.u,
                            pkey=rsa_key)

        scp_client = scp.SCPClient(self.client.get_transport())
        # SCPのputなのかgetなのか
        try:
            if arrstr[1] == 'put':
                scp_client.put(arrstr[2], arrstr[3])
            elif arrstr[1] == 'get':
                scp_client.get(arrstr[2], arrstr[3])
        except FileNotFoundError as e:
            Termout.errmsgout('コピー元 or 先ファイルが存在しません')
            Termout.errmsgout(str(e))
            sys.exit(255)

    def sshcmd(self, cmdline):

        try:
            # コマンドの標準出力 Or 標準エラー出力を捕捉
            stdin, stdout, stderr = self.client.exec_command(cmdline)
            if self.stderrchk(stderr) is True:
                Termout.errmsgout('Cmdline Error!')
                self.client.close
                sys.exit(255)

            self.stdoutread(stdout)
            self.client.close

        except SSHException as e:
            Termout.errmsgout('SSHException Error!')
            Termout.errmsgout(str(e))
            self.client.close
            sys.exit(255)

    # 標準エラー出力のバッファが空かどうかチェック,空でなければエラーとして即リターン
    def stderrchk(self, err):
        buf = err.read()
        # 標準エラー出力除外リストのチェック
        oErr = ErrList()
        flg = "nohit"
        # エラーリストが空であれば、プロパティ属性（_ErrList__errlst）は空でFalse
        if hasattr(oErr, '_ErrList__errlst'):
            for ls in oErr.errlst:
                # 除外リストに該当しているかチェック
                if ls in buf.decode('utf-8'):
                    flg = "hit"
        # エラーバッファが存在し，除外リストにない場合はエラー
        if len(buf) > 0 and flg == "nohit":
            Termout.errmsgout(buf.decode('utf-8'))
            return True
        else:
            # 除外エラーでも一応プリント
            print(buf.decode('utf-8'))
            return False

    # 標準出力をバッファから取り出しコンソール出力
    def stdoutread(self, out):
        for o in out:
            print(o)


if __name__ == '__main__':

    args = sys.argv
    if 2 != len(args):
        Termout.errmsgout("引数エラー: python スクリプト yamlパス")
        sys.exit(255)

    # yaml(定義)を読み込む
    with open(args[1], encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.SafeLoader)
        for indx, val in enumerate(data):
            TRGT = 'TargetCon' + str(indx+1)
            # ConnParm-hostname複数指定があればループ
            hostlist = data[TRGT]['ConnParm'][0].get("hostname").split(',')
            for host in hostlist:
                Termout.greenmsgout("=" * 8 + TRGT + "-" + host + "=" * 8)
                objSsh = SshCon(data[TRGT]['ConnParm'], host)
                rtn = objSsh.sshserverope(data[TRGT]['Operation'])
                if rtn is False:
                    Termout.errmsgout("sshserverope Error!")
                    sys.exit(255)
    Termout.greenmsgout("処理が完了しました")
