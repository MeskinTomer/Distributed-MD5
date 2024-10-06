"""
The Python Class that implements the server
"""

import socket
import threading
from threading import Thread
from Protocol import *

# Socket Constants
QUEUE_SIZE = 1
IP = '0.0.0.0'
PORT = 1779
SOCKET_TIMEOUT = 2

# Decryption Constants
WORK_PER_CORE = 1000000
STR_LENGTH = 10


class Server:
    def __init__(self, encrypted_str: str):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # The Server Socket
        self.threads = []  # Threads list
        self.start = 0  # Start value for next client request
        self.found = False  # Value found flag
        self.encrypted_str = encrypted_str  # String to decrypt
        self.decrypted_str = ''  # The decrypted string
        self.lock = threading.Lock()  # Synchronization Lock
        self.no_more_work = False  # Tracks if all ranges have been assigned
        self.active_clients = 0  # Track active clients processing ranges

    def start_decryption(self):
        try:
            # Set up the server socket
            self.server_socket.bind((IP, PORT))
            self.server_socket.listen(QUEUE_SIZE)
            self.server_socket.settimeout(SOCKET_TIMEOUT)

            # Client Accepting Loop
            while not self.found and (not self.no_more_work or self.active_clients > 0):
                try:
                    client_socket, addr = self.server_socket.accept()
                    with self.lock:
                        self.active_clients += 1  # Increment active clients

                    # Start Client Thread
                    thread = Thread(target=self.handle_client, args=(client_socket,))
                    thread.start()
                    self.threads.append(thread)
                except socket.timeout:
                    pass
        except socket.error as err:
            print('received socket exception - ' + str(err))
        finally:
            # Thread joining
            for thread in self.threads:
                thread.join(timeout=5)

            self.server_socket.close()  # Closing Server Socket

            if not self.found:
                print("No decryption result found.")
            else:
                print("Decryption result found")
            return self.decrypted_str

    def handle_client(self, client_socket: socket):
        try:
            while not self.found:
                try:
                    # Receive Data
                    cmd, data = protocol_receive(client_socket)

                    if cmd is None:  # Detect client disconnection
                        break  # Client disconnected

                    match cmd:
                        case 'Req':
                            # Get Range
                            cores = int(data)
                            start, end = self.get_range(cores)
                            if not self.no_more_work:
                                # Send Response
                                response_command = 'Job'

                                start_str = str(start).zfill(STR_LENGTH)
                                end_str = str(end).zfill(STR_LENGTH)
                                response_data = start_str + end_str + self.encrypted_str
                                protocol_send(client_socket, response_command, response_data)
                            else:
                                # No more work
                                protocol_send(client_socket, 'Job', ('0' * STR_LENGTH) * 2)
                                break
                        case 'Res':
                            if data[:5] == 'found':
                                with self.lock:
                                    self.found = True
                                    self.decrypted_str = data[5:].zfill(STR_LENGTH)
                            if data[:5] == 'notfd':
                                pass
                except socket.timeout:
                    pass
        except (ConnectionResetError, BrokenPipeError) as err:
            print("Client disconnected unexpectedly - " + err)
        finally:
            # Decrement active clients once this client is done
            try:
                client_socket.close()
            except Exception as e:
                print(f"Error closing client socket: {e}")
            finally:
                # Decrement active clients once this client is done
                with self.lock:
                    self.active_clients -= 1

    def get_range(self, cores: int):
        with self.lock:
            if self.start < 10 ** STR_LENGTH:
                start = self.start
                end = start + cores * WORK_PER_CORE - 1
                if end > 10 ** (STR_LENGTH + 1) - 1:
                    end = 10 ** (STR_LENGTH + 1) - 1
                self.start = end + 1
            else:
                start = 0
                end = 0
                self.no_more_work = True
        return start, end


if __name__ == '__main__':
    server = Server('ec9c0f7edcc18a98b1f31853b1813301')
    decrypted_string = server.start_decryption()
    print(server.start_decryption())

    # Asserts after the server runs
    assert isinstance(decrypted_string, str), "Decrypted result should be a string"
    assert len(decrypted_string) == STR_LENGTH, f"Decrypted string should have length {STR_LENGTH}"
    print("All assertions passed.")
