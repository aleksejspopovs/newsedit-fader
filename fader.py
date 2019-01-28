import binascii
import code

import ftdi1 as ftdi

KEY_CODES = {
    0x4a: 'slider',
    0x49: 'pan',
    0x48: 'gang',
    0x47: 'solo',
    0x46: 'mute',
    0x70: 'clear',
    0x71: 'write',
    0x72: 'show',
    0x73: 'master',
}

def parse_msg(data):
    # takes first packet, returns remainder of data

    if len(data) < 2:
        return data

    channel = data[0] - 0xb0
    assert (0 <= channel <= 7)

    msg_type = data[1]
    msg_class = data[1] >> 4

    if msg_class == 0x0:
        # slider
        assert msg_type == 0x07
        if len(data) < 5:
            return data

        high, twenty_seven, low, *rest = data[2:]
        assert twenty_seven == 0x27
        assert low in [0x00, 0x40]
        assert 0x00 <= high <= 0x7f

        value = (high << 1) | (low >> 6)
        print('slider {} to {}'.format(channel, value))

        return rest
    elif msg_class == 0x4:
        # channel button
        assert msg_type in KEY_CODES

        if len(data) < 3:
            return data

        event, *rest = data[2:]
        assert event in [0x00, 0x7f]

        print('{} on channel {}: {}'.format(
            KEY_CODES[msg_type],
            channel,
            'down' if event == 0x7f else 'up'
        ))
        return rest
    elif msg_class == 0x7:
        # global button
        assert channel == 0
        assert msg_type in KEY_CODES

        if len(data) < 3:
            return data

        event, *rest = data[2:]
        assert event in [0x00, 0x7f]

        print('{}: {}'.format(
            KEY_CODES[msg_type],
            'down' if event == 0x7f else 'up'
        ))
        return rest
    else:
        assert False, 'unknown msg class {}'.format(msg_class)

def construct_msg_slider(channel, value):
    assert 0 <= channel <= 7
    assert 0 <= value <= 255
    return bytes([
        0xb0 | channel,
        0x07,
        value >> 1,
        0x27,
        (value & 1) << 6,
    ])

def construct_msg_led(channel, keycode, value):
    assert 0 <= channel <= 7
    assert keycode in KEY_CODES
    assert isinstance(value, bool)

    return bytes([
        0xb0 | channel,
        keycode,
        0x7f if value else 0x00
    ])

def send_msg_slider(ctx, channel, value):
    msg = construct_msg_slider(channel, value)
    ftdi.write_data(ctx, msg)

def send_msg_led(ctx, channel, keycode, value):
    msg = construct_msg_led(channel, keycode, value)
    ftdi.write_data(ctx, msg)

def parse_continuously(ctx):
    buf = []
    try:
        while True:
            size, buf_add = ftdi.read_data(ctx, 256)
            if size == 0:
                continue

            buf.extend(buf_add[:size])
            while True:
                new_buf = parse_msg(buf)
                if new_buf != buf:
                    buf = new_buf
                else:
                    break
    except KeyboardInterrupt:
        pass

def read_continuously(ctx, verbose=True):
    try:
        while True:
            size, buf = ftdi.read_data(ctx, 256)
            if size == 0:
                continue

            hexed = binascii.hexlify(buf[:size]).decode('ascii')
            if verbose:
                print(size, hexed)
            else:
                print(hexed, end='')
    except KeyboardInterrupt:
        print()

def bruteforce_properties(ctx):
    for bits in [ftdi.BITS_8]: #[ftdi.BITS_7, ftdi.BITS_8]:
        for sbit in [ftdi.STOP_BIT_1, ftdi.STOP_BIT_15, ftdi.STOP_BIT_2]:
            for parity in [ftdi.NONE]: #, ftdi.ODD, ftdi.EVEN, ftdi.MARK, ftdi.SPACE]:
                for break_ in [ftdi.BREAK_OFF, ftdi.BREAK_ON]:
                    print(bits, sbit, parity, break_)
                    ftdi.set_line_property2(ctx, bits, sbit, parity, break_)

                    cnt = 0
                    while cnt < 4:
                        size, buf = ftdi.read_data(ctx, 256)
                        if size == 0:
                            continue

                        print(size, binascii.hexlify(buf[:size]).decode('ascii'))
                        cnt += 1

                    print()

def main():
    ctx = ftdi.new()

    ret = ftdi.usb_open(ctx, 0x0760, 0x0002)
    assert ret == 0, 'ftdi.usb_open error: {}'.format(ret)

    ret = ftdi.set_baudrate(ctx, 38400)
    assert ret == 0, 'baudrate error'

    try:
        code.interact(
            local={
                'ctx': ctx,
                'ftdi': ftdi,
                'read_continuously': read_continuously,
                'parse_continuously': parse_continuously,
                'send_msg_slider': send_msg_slider,
                'send_msg_led': send_msg_led,
                'bruteforce_properties': bruteforce_properties,
            },
            banner='ftdi & ctx imported',
            exitmsg='cleaning up!')
    finally:
        ftdi.free(ctx)
        print('done')

def bruteforce_connection_props():
    for bits in [ftdi.BITS_8]: #[ftdi.BITS_7, ftdi.BITS_8]:
        for sbit in [ftdi.STOP_BIT_1, ftdi.STOP_BIT_15, ftdi.STOP_BIT_2]:
            for parity in [ftdi.NONE, ftdi.ODD, ftdi.EVEN, ftdi.MARK, ftdi.SPACE]:
                for break_ in [ftdi.BREAK_ON]: #, ftdi.BREAK_OFF]:
                    print(bits, sbit, parity, break_)
                    ctx = ftdi.new()
                    ret = ftdi.usb_open(ctx, 0x0760, 0x0002)
                    assert ret == 0
                    ret = ftdi.set_baudrate(ctx, 38400)
                    assert ret == 0, 'baudrate error'

                    ftdi.set_line_property2(ctx, bits, sbit, parity, break_)

                    send_msg_led(ctx, 2, 0x49, True)

                    input('waiting')

                    ftdi.free(ctx)

if __name__ == '__main__':
    main()
    # bruteforce_connection_props()
