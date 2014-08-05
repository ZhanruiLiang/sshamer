import os
import sys
import signal
from time import sleep
from datetime import datetime

import pexpect

from .socksclient import Client, ResponseStatus


class ProxyServer:
    """
    Example config:
    {
        'addr':'myvps.com',
        'port':'22',
        'user':'bobby',
        'passwd':'secret',
        'local_port': 7070,
        'timeout': 5,
    }

    Default config path: ~/.sshammer

    Custom config: 
    Run: 
        sshamer /path/to/config_file

    """

    SSH_CMD = 'ssh -N -D {local_port} {user}@{addr} -p {port} -F {ssh_config_path}'
    REQUIRED_ATTR = ['user', 'passwd', 'local_port', 'addr', 'port']
    CHECK_INTERVAL = 3

    def __init__(self, config):
        for attr in self.REQUIRED_ATTR:
            if attr not in config:
                raise Exception('Attribute {} is not presented in config'.format(attr))
        self.config = config
        self._quit = False
        self.ssh = None

    def log(self, *args):
        print(datetime.now().strftime('[%H:%M:%S]'), *args)

    def start(self):
        config = self.config.copy()
        config['ssh_config_path'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'ssh_config'
        )
        cmd = self.SSH_CMD.format(**config)
        self.log(cmd)
        while not self._quit:
            self.log('Connecting...')
            if self.ssh:
                self.ssh.terminate()
            ssh = self.ssh = pexpect.spawn(cmd)
            try:
                e = ssh.expect(['password:', '(yes/no)', pexpect.EOF], timeout=self.config['timeout'])
            except pexpect.TIMEOUT:
                self.log('Timeout')
                continue
            if e == 0:
                ssh.sendline(config['passwd'])
                self.log('Sent password')
                self.wait_connect()
                self.log('Connected')
                # self.keep()
                self.menu()
            elif e == 1:
                ssh.sendline('yes')
            elif e == 2:
                self.log('Received EOF')
            sleep(0.5)
        return self

    def _on_sigint(self, *args):
        self.log('Quitting...')
        self._quit = True

    TEST_SITES = [
        'google.com',
        'bing.com',
    ]
    TEST_MESSAGE = 'GET /\nUser-Agent: Mozilla/5.0 (X11; Linux i686; rv:30.0) Gecko/20100101 Firefox/30.0\n\n'.encode()

    def wait_connect(self):
        while not self._quit:
            try:
                client = Client(int(self.config['local_port']))
                client.close()
                return
            except ConnectionRefusedError:
                pass

    def menu(self):
        while 1:
            choice = input('0) Reconnect; 1) exit. Your choice:')
            if choice == '0':
                return
            elif choice == '1':
                self._quit = True
                return
            print('Invalid choice.')

    def keep(self):
        # signal.signal(signal.SIGINT, self._on_sigint)
        self.log('Ready')
        try:
            while not self._quit:
                fine = True
                for site in self.TEST_SITES:
                    fine = True
                    try:
                        client = Client(int(self.config['local_port']))
                        response = client.connect(site, 80)
                        assert response.status is ResponseStatus.REQUEST_GRANTED
                        msg_send = self.TEST_MESSAGE
                        client.sock.send(msg_send)
                        # self.log('{} << {}'.format(site, msg_send))
                        msg_recv = client.sock.recv(1)
                        # self.log('{} >> {}'.format(site, msg_recv))
                        client.close()
                        sleep(self.CHECK_INTERVAL)
                        break
                    except:
                        import traceback
                        traceback.print_exc()
                        fine = False
                if not fine:
                    return
        finally:
            if self.ssh:
                self.ssh.terminate()
                self.ssh = None
                self.log('Disconnected')


def get_default_config_path():
    return os.path.expanduser('~/.sshammer')


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else get_default_config_path()
    config = eval(open(config_path).read())
    ProxyServer(config).start()


if __name__ == '__main__':
    main()
