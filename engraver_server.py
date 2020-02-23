import RPi.GPIO as GPIO
import lcddriver
import threading
import socket
import time

engraver = {
    'pins': {
        'laser': {
            '1': 12,
            '2': 11
        },
        'x': {
            'pul': 4,
            'dir': 5
        },
        'y': {
            'pul': 6,
            'dir': 7
        },
        'z': {
            'pul': 8,
            'dir': 9
        },
        'end': 10,
        'lcd': {
            'sda': 2,
            'scl': 3
        },
        'buzzers': 13
    },
    'pos': {
        'x': 0,
        'y': 0,
        'z': 0
    },
    'delay': {
        'x': 0.001,
        'y': 0.001,
        'z': 0.001
    },
    'block': True
}

def engraver_config():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(engraver['pins']['laser']['1'], GPIO.OUT)
    GPIO.setup(engraver['pins']['laser']['2'], GPIO.OUT)
    GPIO.output(engraver['pins']['laser']['1'], GPIO.LOW)
    GPIO.output(engraver['pins']['laser']['2'], GPIO.LOW)

    GPIO.setup(engraver['pins']['x']['pul'], GPIO.OUT)
    GPIO.setup(engraver['pins']['x']['dir'], GPIO.OUT)
    GPIO.output(engraver['pins']['x']['pul'], GPIO.LOW)
    GPIO.output(engraver['pins']['x']['dir'], GPIO.LOW)

    GPIO.setup(engraver['pins']['y']['pul'], GPIO.OUT)
    GPIO.setup(engraver['pins']['y']['dir'], GPIO.OUT)
    GPIO.output(engraver['pins']['y']['pul'], GPIO.LOW)
    GPIO.output(engraver['pins']['y']['dir'], GPIO.LOW)

    GPIO.setup(engraver['pins']['z']['pul'], GPIO.OUT)
    GPIO.setup(engraver['pins']['z']['dir'], GPIO.OUT)
    GPIO.output(engraver['pins']['z']['pul'], GPIO.LOW)
    GPIO.output(engraver['pins']['z']['dir'], GPIO.LOW)

    GPIO.setup(engraver['pins']['end'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def engraver_moveX(dir, count):
    GPIO.output(engraver['pins']['x']['dir'], dir)

    for x in range(count):
        if (GPIO.input(10) == GPIO.LOW) and (engraver['block']):
            print("Calibration is required!")
            return False

        GPIO.output(engraver['pins']['x']['pul'], GPIO.HIGH)
        time.sleep(engraver['delay']['x'])
        GPIO.output(engraver['pins']['x']['pul'], GPIO.LOW)
        time.sleep(engraver['delay']['x'])

        if (dir == GPIO.HIGH):
            engraver['pos']['x'] -= 1

        elif (dir == GPIO.LOW):
            engraver['pos']['x'] += 1

    return True

def engraver_moveY(dir, count):
    GPIO.output(engraver['pins']['y']['dir'], dir)

    for x in range(count):
        if (GPIO.input(10) == GPIO.LOW) and (engraver['block']):
            print("Calibration is required!")
            return False

        GPIO.output(engraver['pins']['y']['pul'], GPIO.HIGH)
        time.sleep(engraver['delay']['y'])
        GPIO.output(engraver['pins']['y']['pul'], GPIO.LOW)
        time.sleep(engraver['delay']['y'])

        if (dir == GPIO.LOW):
            engraver['pos']['y'] -= 1

        elif (dir == GPIO.HIGH):
            engraver['pos']['y'] += 1

    return True

def engraver_moveZ(dir, count):
    GPIO.output(engraver['pins']['z']['dir'], dir)

    for x in range(count):
        if (GPIO.input(10) == GPIO.LOW) and (engraver['block']):
            print("Calibration is required!")
            return False

        GPIO.output(engraver['pins']['z']['pul'], GPIO.HIGH)
        time.sleep(engraver['delay']['z'])
        GPIO.output(engraver['pins']['z']['pul'], GPIO.LOW)
        time.sleep(engraver['delay']['z'])

        if (dir == GPIO.HIGH):
            engraver['pos']['z'] -= 1

        elif (dir == GPIO.LOW):
            engraver['pos']['z'] += 1

    return True

def engraver_laser(mode):
    GPIO.output(engraver['pins']['laser']['1'], mode)

HOST = '192.168.0.1'
PORT = 29000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(10)

def send_message(socket, message):
    packet = "\x5f\x5f\x5e\x5f\x5f"
    packet += str(chr(len(message)))
    packet += message

    socket.sendto(packet.encode(), (HOST, PORT))

def read_packet(socket):
    message = ""

    packet_pattern = "\x5f\x5f\x5e\x5f\x5f"

    while True:
        message += socket.recv(1).decode()

        if len(message) <= 5:
            continue

        if packet_pattern in message:
            while True:
                try:
                    packet_length = bytearray(message[message.index(packet_pattern) + len(packet_pattern)].encode())[0]
                    break
                except IndexError:
                    message += socket.recv(1).decode()
                    continue

            for x in range(packet_length):
                message += socket.recv(1).decode()

            return message[message.index(packet_pattern)+len(packet_pattern)+1:]

def client_handler(conn):
    while True:
        data = read_packet(conn)

        if data == 'close':
            send_message(conn, "close")
            break

        elif data == 'x':
            send_message(conn, "x="+str(engraver['pos']['x']))

        elif data == 'y':
            send_message(conn, "y="+str(engraver['pos']['y']))

        elif data == 'z':
            send_message(conn, "z="+str(engraver['pos']['z']))

        elif data.find('=') >= 0:
            cmd = data.partition('=')[0]
            info = data.partition('=')[2]

            if cmd == 'laser':
                if info == 'on':
                    print("Laser ON!")
                    engraver_laser(GPIO.HIGH)
                elif info == 'off':
                    print("Laser OFF!")
                    engraver_laser(GPIO.LOW)

            elif cmd == 'buzzers':
                GPIO.output(engraver['pins']['buzzers'], GPIO.HIGH)
                time.sleep(float(info))
                GPIO.output(engraver['pins']['buzzers'], GPIO.LOW)

            elif cmd == 'lcd':
                if info == 'clear':
                    mylcd.lcd_clear()

            elif cmd == 'lcd1':
                mylcd.lcd_display_string(info, 1)

            elif cmd == 'lcd2':
                mylcd.lcd_display_string(info, 2)

            elif cmd == 'cali':
                if info == 'on':
                    print("Calibration ON!")
                    engraver['block'] = False
                elif info == 'off':
                    print("Calibration OFF")
                    engraver['block'] = True

            elif cmd == 'dx':
                print("New delay for X: ", float(info))
                engraver['delay']['x'] = float(info)

            elif cmd == 'dy':
                print("New delay for Y: ", float(info))
                engraver['delay']['y'] = float(info)

            elif cmd == 'dz':
                print("New delay for Z: ", float(info))
                engraver['delay']['z'] = float(info)

            send_message(conn, data)

        elif data.find('+') >= 0:
            cmd = data.partition('+')[0]
            quantity = data.partition('+')[2]

            if cmd == 'x':
                print("Move X forward by ", int(quantity))
                if not engraver_moveX(GPIO.LOW, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

            elif cmd == 'y':
                print("Move Y forward by ", int(quantity))
                if not engraver_moveY(GPIO.HIGH, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

            elif cmd == 'z':
                print("Move Z forward by ", int(quantity))
                if not engraver_moveZ(GPIO.LOW, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

        elif data.find('-') >= 0:
            cmd = data.partition('-')[0]
            quantity = data.partition('-')[2]

            if cmd == 'x':
                print("Move X backward by ", int(quantity))
                if not engraver_moveX(GPIO.HIGH, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

            elif cmd == 'y':
                print("Move Y backward by ", int(quantity))
                if not engraver_moveY(GPIO.LOW, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

            elif cmd == 'z':
                print("Move Z backward by ", int(quantity))
                if not engraver_moveZ(GPIO.HIGH, int(quantity)):
                    send_message(conn, "cali")
                else:
                    send_message(conn, data)

    conn.close()

engraver_config()

mylcd = lcddriver.lcd()
mylcd.lcd_clear()
mylcd.lcd_display_string("Gotowy", 1)

GPIO.setup(engraver['pins']['buzzers'], GPIO.OUT)
GPIO.output(engraver['pins']['buzzers'], GPIO.LOW)

while True:
    conn, addr = s.accept()

    t = threading.Thread(target=client_handler, args=[conn])
    t.daemon = True
    t.start()