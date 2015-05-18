__author__ = 'frza'

import socket
import msgpack


class IotpTcpClient(object):
    def __init__(self, host, port):
        self._sock = socket.socket()
        self._sock.connect((host, port))

    def close(self):
        self._sock.close()

    def _call(self, data):
        m = msgpack.packb(data)
        self._sock.send(m)

        b = self._sock.recv(1000)
        return msgpack.unpackb(b)

    def send_img_job(self, image_contents):
        return self._call({'type': 'image', 'image_file': image_contents})

    def send_simpletext_job(self, text, wrap=False):
        return self._call({'type': 'simple_text', 'text': text, 'wrap': wrap})

    def query_job_state(self, job_id):
        return self._call({'type': 'query_job_state', 'job_id': job_id})
