import struct
import enum
import socket
from collections import namedtuple

Request = namedtuple('Request', [
    'command',
    'port',
    'host',
])


Response = namedtuple('Response', [
    'version',
    'status',
    'address_type',
    'address',
    'port',
])


class AddressType(enum.IntEnum):
    IPV4 = 0x01
    DOMAIN_NAME = 0x03
    IPV6 = 0x04


class RequestCommand(enum.IntEnum):
    CONNECT = 0x1
    BIND = 0x2
    UDP_ASSOCIATE = 0x3


class ResponseStatus(enum.IntEnum):
    REQUEST_GRANTED = 0
    GENERAL_FAILURE = 1
    CONNECTION_NOT_ALLOWED_BY_RULESET = 2
    NETWORK_UNREACHABLE = 3
    HOST_UNREACHABLE = 4
    CONNECTION_REFUSED = 5
    TTL_EXPIRED = 6
    COMMAND_NOT_SUPPORTED = 7
    ADDRESS_TYPE_NOT_SUPPORTED = 8


class Client:
    def __init__(self, port, host='127.0.0.1'):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self._wfile = self.sock.makefile('wb')
        self._rfile = self.sock.makefile('rb')
        assert self.authenticate()

    def close(self):
        self.sock.close()

    def authenticate(self):
        self._wfile.write(b'\x05\x01\x00')
        self._wfile.flush()
        response = self._rfile.read(2)
        return response == b'\x05\x00'

    def connect(self, host, port):
        self.send_request(Request(
            command=RequestCommand.CONNECT,
            port=port,
            host=host,
        ))
        return self.recv_response(RequestCommand.CONNECT)

    def send_request(self, request):
        r = request
        # B(version)B(command)xB(address type)B(domain name length)ns(domain name)H(port)
        host = r.host.encode()
        msg_send = struct.pack(
            '!BBxBB{}sH'.format(len(host)),
            5, r.command, AddressType.DOMAIN_NAME, len(host), host, r.port)
        self._wfile.write(msg_send)
        self._wfile.flush()

    RESPONSE_PATTERN = '!BBxB'
    RESPONSE_PATTERN_SIZE = struct.calcsize(RESPONSE_PATTERN)

    def recv_response(self, command):
        if command is RequestCommand.CONNECT:
            version, status, address_type = struct.unpack(
                self.RESPONSE_PATTERN,
                self._rfile.read(self.RESPONSE_PATTERN_SIZE)
            )
            status = ResponseStatus(status)
            address_type = AddressType(address_type)
            if address_type is AddressType.IPV4:
                address = self._rfile.read(4)
                address = '.'.join(map(str, address))
            elif address_type is AddressType.DOMAIN_NAME:
                address_len = self._rfile.read(1)[0]
                address = self._rfile.read(address_len).decode()
            elif address_type is AddressType.IPV6:
                address = self._rfile.read(16)
                address = ':'.join('%02x' % x for x in address)
            port, = struct.unpack('!H', self._rfile.read(2))
            return Response(
                version=version,
                status=status,
                address_type=address_type,
                address=address,
                port=port,
            )
        else:
            raise NotImplementedError()
