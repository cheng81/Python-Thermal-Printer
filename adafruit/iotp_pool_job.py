from __future__ import print_function
__author__ = 'frza'
import uuid
import textwrap
import time
from StringIO import StringIO
from PIL import Image


def create_job(obj):
    t = obj.get('type', None)
    if t is None:
        return None
    if t == 'simple_text':
        return SimpleTextJob(text=obj.get('text', ''), wrap=obj.get('wrap', False))
    elif t == 'image':
        return ImageJob(image=Image.open(StringIO(obj.get('image_file'))))
    elif t == 'richtext':
        return RichTextJob(commands=obj.get('commands', []))
    return None


class BaseJob(object):
    def __init__(self):
        self._id = uuid.uuid4()
        self._state = 'created'
        self._ts = -1

    def queued(self):
        self._state = 'queued'

    @property
    def remove(self):
        return self.state == 'done' and int(time.time()) - self._ts > 30 * 60 * 1000

    @property
    def id(self):
        return self._id

    @property
    def id_str(self):
        return str(self._id)

    @property
    def state(self):
        return self._state

    def run(self, printer):
        if self._state == 'queued':
            self._state = 'running'
            try:
                self._with_printer(printer)
            except Exception:
                import logging
                logging.exception("Error executing job {}", self.id_str)
            self._state = 'done'
            self._ts = int(time.time())

    def _with_printer(self, printer):
        raise Exception('implement-me')


class SimpleTextJob(BaseJob):
    def __init__(self, text, wrap=True):
        super(SimpleTextJob, self).__init__()
        self._text = text
        self._wrap = wrap

    def _with_printer(self, printer):
        if self._wrap:
            wrapped = textwrap.wrap(self._text, width=32)
        else:
            wrapped = [self._text]
        for line in wrapped:
            printer.print(line + '\n')


class ImageJob(BaseJob):
    def __init__(self, image):
        super(ImageJob, self).__init__()
        self._image = image

    def _with_printer(self, printer):
        img = self._pre_process()
        printer.printImage(img)
        # remove image object immediately
        self._image = None

    def _pre_process(self):
        img = self._image
        if img.mode != '1' or img.mode != 'L':
            img = img.convert(mode='1')

        # resize if w and h > 384
        w, h = img.size
        if w > 384 and h > 384:
            if w > h:
                h1 = 384
                w1 = w * h1 / h
            else:
                w1 = 384
                h1 = w1 * h / w
            img = img.resize((w1, h1))

        # rotate if w > 384
        w, _ = img.size
        if w > 384:
            img = img.rotate(90)

        return img


class RichTextJob(BaseJob):
    def __init__(self, commands):
        super(RichTextJob, self).__init__()
        self._commands = commands

    def _with_printer(self, printer):
        for c in self._commands:
            self._exec(c, printer)
        self._commands = None

    @staticmethod
    def _exec(cmd, printer):
        if isinstance(cmd, str):
            code = cmd
            args = None
        else:
            code = cmd['code']
            args = cmd['args']
        m = getattr(printer, code, None)
        if m is None:
            return
        if args is None:
            # only needs the self param
            m()
        else:
            # call with cmd arg
            m(*args)

# all methods
# ===========
# timeoutSet(x)
# timeoutWait
# setTimes(p, f)
# writeBytes(*args)
# write(*data)
# begin(heatTime=defaultHeatTime)
# reset
# setDefault
# test
# printBarcode(text, type)
# setBarcodeHeight(val=50)
# setPrintMode(mask)
# unsetPrintMode(mask)
# writePrintMode
# normal
# inverseOn
# inverseOff
# upsideDownOn
# upsideDownOff
# doubleHeightOn
# doubleHeightOff
# doubleWidthOn
# doubleWidthOff
# strikeOn
# strikeOff
# boldOn
# boldOff
# justify(value)
# feed(x=1)
# feedRows(rows)
# flush
# setSize(value)
# underlineOn(weight=1)
# underlineOff
# printBitmap(w, h, bitmap, LaaT=False)
# printImage(image, LaaT=False)
# offline
# online
# sleep
# sleepAfter(seconds)
# wake
# setLineHeight(val=32)
# print(*args, **kwargs)
# println(*args, **kwargs)

# usable methods
# ==============
# reset
# setDefault
# printBarcode(text, type)
# setBarcodeHeight(val=50)
# normal
# inverseOn
# inverseOff
# upsideDownOn
# upsideDownOff
# doubleHeightOn
# doubleHeightOff
# doubleWidthOn
# doubleWidthOff
# strikeOn
# strikeOff
# boldOn
# boldOff
# justify(value)
# feed(x=1)
# feedRows(rows)
# setSize(value)
# underlineOn(weight=1)
# underlineOff
# printBitmap(w, h, bitmap, LaaT=False)
# printImage(image, LaaT=False)
# setLineHeight(val=32)
# print(*args, **kwargs)
# println(*args, **kwargs)
#
# barcode types:
# UPC_A   =  0
# UPC_E   =  1
# EAN13   =  2
# EAN8    =  3
# CODE39  =  4
# I25     =  5
# CODEBAR =  6
# CODE93  =  7
# CODE128 =  8
# CODE11  =  9
# MSI     = 10
#
# justify values:
# c, r, l
#
# setSize values:
# l, m, s

# sample:
# ['inverseOn', {'code':'println', 'args': ["helo!"]}, 'inverseOff',
#  {'code':'print', 'args':["here are some", "lines of text."]}]
