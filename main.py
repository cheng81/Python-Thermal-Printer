from __future__ import print_function
__author__ = 'frza'

from adafruit import iotp_pool
from adafruit.tcp_interface import IotpTCPServer
from adafruit.amqp_interface import IotpAMQPServer
import time
import signal


class TestPrinter():
    def __init__(self):
        print("Test printer instantiated")

    def print(self, line):
        print(">> {}".format(line))

    def printImage(self, img):
        print(">> IMG")

    def feed(self, _how_much):
        print("(line feed)")


ledPin       = 18
buttonPin    = 23
holdTime     = 2     # Duration for button hold (shutdown)
tapTime      = 0.01  # Debounce time for button taps


def setup(printer):
    import RPi.GPIO as GPIO

    # Initialization

    # Use Broadcom pin numbers (not Raspberry Pi pin numbers) for GPIO
    GPIO.setmode(GPIO.BCM)

    # Enable LED and button (w/pull-up on latter)
    GPIO.setup(ledPin, GPIO.OUT)
    GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # LED on while working
    GPIO.output(ledPin, GPIO.HIGH)

    # Processor load is heavy at startup; wait a moment to avoid
    # stalling during greeting.
    time.sleep(30)

    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 0))
        printer.print('My IP address is ' + s.getsockname()[0])
        printer.feed(3)
    except:
        printer.boldOn()
        printer.println('Network is unreachable.')
        printer.boldOff()
        printer.print('Connect display and keyboard\n'
          'for network troubleshooting.')
        printer.feed(3)
        exit(0)


def loop(state, printer):
    import RPi.GPIO as GPIO
    # Poll current button state and time
    buttonState = GPIO.input(buttonPin)
    t = time.time()

    # Has button state changed?
    if buttonState != state['prevButtonState']:
        state['prevButtonState'] = buttonState   # Yes, save new state/time
        state['prevTime'] = t
    else:                             # Button state unchanged
        if (t - state['prevTime']) >= holdTime:  # Button held more than 'holdTime'?
            # Yes it has.  Is the hold action as-yet untriggered?
            if state['holdEnable'] == True:        # Yep!
                hold(printer)                      # Perform hold action (usu. shutdown)
                state['holdEnable'] = False          # 1 shot...don't repeat hold action
                state['tapEnable'] = False          # Don't do tap action on release
        elif (t - state['prevTime']) >= tapTime: # Not holdTime.  tapTime elapsed?
            # Yes.  Debounced press or release...
            if buttonState == True:       # Button released?
                if state['tapEnable'] == True:       # Ignore if prior hold()
                    # tap()                     # Tap triggered (button released)
                    state['tapEnable'] = False        # Disable tap and hold
                    state['holdEnable'] = False
        else:                         # Button pressed
            state['tapEnable'] = True           # Enable tap and hold actions
            state['holdEnable'] = True

    # LED blinks while idle, for a brief interval every 2 seconds.
    # Pin 18 is PWM-capable and a "sleep throb" would be nice, but
    # the PWM-related library is a hassle for average users to install
    # right now.  Might return to this later when it's more accessible.
    if ((int(t) & 1) == 0) and ((t - int(t)) < 0.15):
        GPIO.output(ledPin, GPIO.HIGH)
    else:
        GPIO.output(ledPin, GPIO.LOW)


# Called when button is held down.  Prints image, invokes shutdown process.
def hold(printer):
    import RPi.GPIO as GPIO
    import subprocess
    GPIO.output(ledPin, GPIO.HIGH)
    printer.println('Bye!')
    printer.feed(3)
    subprocess.call("sync")
    subprocess.call(["shutdown", "-h", "now"])
    GPIO.output(ledPin, GPIO.LOW)


def main(config):
    if config['printer_type'] == 'test':
        printer = TestPrinter()
        state = None

        loop_ = lambda _state ,_printer: time.sleep(1)
    else:
        import RPi.GPIO as GPIO
        from adafruit.Adafruit_Thermal import Adafruit_Thermal
        printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
        setup(printer)
        state = {'prevButtonState': GPIO.input(buttonPin),
             'prevTime': time.time(),
             'tapEnable': False,
             'holdEnable': False}

        loop_ = loop

    iotp_pool.init(printer)
    # start servers
    tcp_intf = IotpTCPServer(config)
    tcp_intf.start()

    amqp_intf = IotpAMQPServer(config)
    amqp_intf.start()

    # Poll initial button state and time

    while iotp_pool.is_running():
        loop_(state, printer)

    tcp_intf.stop()
    amqp_intf.stop()


def activate_signal_handler(signal_handler_fun):
    '''
    Registers the given signal handler for a number of signals that may be sent to the process.
    signal_handler_fun: A function object with a signature like
    def f(signal_number, stack_frame): ...
    '''
    for s in [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGABRT, signal.SIGTERM]:
        signal.signal(s, signal_handler_fun)


if __name__ == '__main__':
    def exit_handler(signum, frame):
        iotp_pool.teardown()
        print("Exiting")

    activate_signal_handler(exit_handler)

    c = {'printer_type': 'test',
         # tcp props
         'TCP_HOST': '0.0.0.0',
         'TCP_PORT': 9999,
         # amqp props
         'AMQP_HOST': 'localhost'
        }
    main(c)
