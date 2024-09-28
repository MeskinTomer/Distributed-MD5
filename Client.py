"""
The Python Class that implements the server
"""

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
    def __init__(self, cores):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.threads = []
        self.found = False
        self.no_work = False
        self.lock = threading.Lock()
        self.cores = cores
        self.decrypted_message = ''

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

    def decrypt_md5(self, start, end, encrypted_message):
        for num in range(start, end):
            cur_num = str(num).zfill(STR_LENGTH)
            cur_num_md5 = hashlib.md5(cur_num.encode())
            cur_num_hex = cur_num_md5.hexdigest()

            if num == 342:
                print(str(cur_num_hex))
                print(encrypted_message)

            if cur_num_hex == encrypted_message:
                with self.lock:
                    self.found = True
                    self.decrypted_message = str(num)
                print(f'Found original: {cur_num}')
                break

        if not self.found:
            print(f'Original Num not in range: {start} - {end}')



