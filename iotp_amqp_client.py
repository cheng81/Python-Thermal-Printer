__author__ = 'frza'

import pika
import uuid
import msgpack


class IotpAmqpClient(object):
    def __init__(self, host, rk):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))

        self._rk = rk
        self.response = None

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, _ch, _method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def _call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self._rk,
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id),
                                   body=msgpack.packb(n))
        while self.response is None:
            self.connection.process_data_events()
        return msgpack.unpackb(self.response)

    def send_img_job(self, image_contents):
        return self._call({'type': 'image', 'image_file': image_contents})

    def send_simpletext_job(self, text, wrap=False):
        return self._call({'type': 'simple_text', 'text': text, 'wrap': wrap})

    def send_richtext_job(self, commands):
        return self._call({'type': 'richtext', 'commands': commands})

    def query_job_state(self, job_id):
        return self._call({'type': 'query_job_state', 'job_id': job_id})


class RichTextBuilder(object):
    JUSTIFY_CENTER = 'c'
    JUSTIFY_LEFT = 'l'
    JUSTIFY_RIGHT = 'r'

    SIZE_LARGE = 'l'
    SIZE_MEDIUM = 'm'
    SIZE_SMALL = 's'

    UPC_A = 0
    UPC_E = 1
    EAN13 = 2
    EAN8 = 3
    CODE39 = 4
    I25 = 5
    CODEBAR = 6
    CODE93 = 7
    CODE128 = 8
    CODE11 = 9
    MSI = 10

    def __init__(self):
        self._o = []

    def _add(self, code, args=None):
        if args is None:
            self._o.append(code)
        else:
            self._o.append({'code': code, 'args': args})
        return self

    @property
    def commands(self):
        return self._o

    def reset(self):
        return self._add('reset')

    def setDefault(self):
        return self._add('setDefault')

    def printBarcode(self, text, type):
        return self._add('printBarcode', [text, type])

    def setBarcodeHeight(self, val=50):
        return self._add('setBarcodeHeight', [val])

    def normal(self):
        return self._add('normal')

    def inverseOn(self):
        return self._add('inverseOn')

    def inverseOff(self):
        return self._add('inverseOff')

    def upsideDownOn(self):
        return self._add('upsideDownOn')

    def upsideDownOff(self):
        return self._add('upsideDownOff')

    def doubleHeightOn(self):
        return self._add('doubleHeightOn')

    def doubleHeightOff(self):
        return self._add('doubleHeightOff')

    def doubleWidthOn(self):
        return self._add('doubleWidthOn')

    def strikeOn(self):
        return self._add('strikeOn')

    def strikeOff(self):
        return self._add('strikeOff')

    def boldOn(self):
        return self._add('boldOn')

    def boldOff(self):
        return self._add('boldOff')

    def justify(self, value):
        return self._add('justify', [value])

    def feed(self, x=1):
        return self._add('feed', [x])

    def feedRows(self, rows):
        return self._add('feedRows', [rows])

    def setSize(self, value):
        return self._add('setSize', [value])

    def underlineOn(self, weight=1):
        return self._add('underlineOn', [weight])

    def underlineOff(self):
        return self._add('underlineOff')

    def printBitmap(self, w, h, bitmap, LaaT=False):
        return self._add('printBitmap', [w, h, bitmap, LaaT])

    def setLineHeight(self, val=32):
        return self._add('setLineHeight', [val])

    def pprint(self, *args):
        return self._add('print', args)

    def println(self, *args):
        return self._add('println', args)
