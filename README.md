# NewsEdit Motorized Fader Controller reverse-engineering

This repo contains reverse-engineered Python code that can interface with the NewsEdit Motorized Fader Controller.

# Requirements

You'll need Python 3 and `libftdi` with its Python bindings. This should work on any OS supported by `libusb` (so at least Linux, Windows, and OS X), but I've only tested it on Linux.

On Linux, you'll need to give yourself the permissions to access the USB device. To do so, create a file called `/etc/udev/rules.d/40-fader.rules` containing just the line `SUBSYSTEMS=="usb", ATTRS{idVendor}=="0760", ATTRS{idProduct}=="0002", MODE="0660", TAG+="uaccess", TAG+="udev-acl"`, then reconnect the fader.

# Running the code

The code doesn't really do anything, it's more of a PoC of something you could extend into a driver if you wanted to. That said, if you run `fader.py`, you'll get a nice interactive console, where you can use `send_msg_slider` or `send_msg_led` to send stuff to the controller, or call `parse_continuously` to parse incoming events.

# Protocol

The fader controller uses an FTDI FT232BL serial-to-USB chip, set to a baud rate of 38400.

The controller has 8 channels, numbered 0 through 7.

When a button that is associated with a channel (pan, gang, solo, mute, as well as the slider itself) is pushed down, the controller sends the hex string `bC 4B 7f`, where `C` is the channel and `B` is the key code. When the button is released, the controller sends `bC 4B 00`.

When a button that is not associated with a channel (clear, write, show, master) is pushed down, the string is `b0 7B 7f`, and when it is released, it's `b0 7B 00`.

When a slider is moved, the string `bC 07 HH 27 L0` is sent. `C` is the channel, `HH` is between `00` and `7f`, `L` is either `0` or `4`, and the new position of the slider (between `00` and `ff`) is calculated as `position = (HH << 1) | (L >> 2)`.

To turn a LED that's located next to a button on, send the same message you'd receive if the button was pressed. To turn it off, send the same message you'd receive if it was released. To move a slider, send the same message you'd receive if it was moved to the desired position (this will not generate a new incoming message).


