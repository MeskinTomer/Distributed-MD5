"""
The Protocol used for communication
"""

import socket


def protocol_send(target_socket, command, data):
    # Zero Filling
    data_length = str(len(data)).zfill(3)

    # Shaping and sending message
    packet = command + data_length + data

    target_socket.send(packet.encode())


def protocol_receive(target_socket: socket):
    # Receiving Packet
    cmd = target_socket.recv(3).decode()

    # Handing Packet
    data_length = int(target_socket.recv(3).decode())
    data = target_socket.recv(data_length).decode()
    return cmd, data
