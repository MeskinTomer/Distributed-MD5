"""
The Python Class that implements the server
"""

# Imports
import socket
import threading
from threading import Thread
from Protocol import *
import hashlib

# Socket Constants
QUEUE_SIZE = 1
IP = '127.0.0.1'
PORT = 1779
SOCKET_TIMEOUT = 2

# Decryption Constants
WORK_PER_CORE = 1000000
STR_LENGTH = 10


class Client:
    def __init__(self, cores: int):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # The Client Socket
        self.threads = []  # Threads list
        self.found = False  # Value found flag
        self.no_work = False  # Flag - all ranges have been assigned
        self.lock = threading.Lock()  # Synchronization Lock
        self.cores = cores  # Amount of the computer's cores
        self.decrypted_message = ''  # The decrypted string

    def start_decryption(self):
        try:
            self.client_socket.connect((IP, PORT))

            while not self.found and not self.no_work:
                # Sends Request for Work
                protocol_send(self.client_socket, 'Req', str(self.cores))
                # Receives Work
                command, data = protocol_receive(self.client_socket)

                overall_start = int(data[:STR_LENGTH])
                overall_end = int(data[STR_LENGTH:STR_LENGTH * 2])

                if overall_end != 0:
                    work_per_core = (overall_end - overall_start + 1) // self.cores
                    encrypted_message = data[STR_LENGTH * 2:]

                    # Distribute Work to Threads
                    for core in range(self.cores):
                        start = overall_start + work_per_core * core
                        end = overall_start + work_per_core * (core + 1)

                        thread = Thread(target=self.decrypt_md5, args=(start, end, encrypted_message))
                        thread.start()
                        self.threads.append(thread)

                    for thread in self.threads:
                        thread.join()

                    response_cmd = 'Res'
                    response_data = ('found' if self.found else 'notfd') + self.decrypted_message

                    protocol_send(self.client_socket, response_cmd, response_data)
                else:
                    self.no_work = True

        except socket.error as error:
            print('received socket error: ' + str(error))
        finally:
            self.client_socket.close()

    def decrypt_md5(self, start: int, end: int, encrypted_message: str):
        for num in range(start, end):
            cur_num = str(num).zfill(STR_LENGTH)
            cur_num_md5 = hashlib.md5(cur_num.encode())
            cur_num_hex = cur_num_md5.hexdigest()

            if cur_num_hex == encrypted_message:
                with self.lock:
                    self.found = True
                    self.decrypted_message = str(num)
                print(f'Found original: {cur_num}')
                break

        if not self.found:
            print(f'Original Num not in range: {start} - {end}')


if __name__ == '__main__':
    client = Client(4)
    client.start_decryption()

    # Asserts after decryption
    if client.found:
        assert client.decrypted_message.isdigit(), "Decrypted message should be a numeric string"
        assert len(client.decrypted_message) == STR_LENGTH, f"Decrypted message should have length {STR_LENGTH}"
        print("Decryption successful:", client.decrypted_message)
    else:
        assert client.no_work, "Client should only stop if no work is available"
        print("No decryption result found")