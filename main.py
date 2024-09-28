import hashlib

cur_num = '342'.zfill(4)
cur_num_md5 = hashlib.md5(cur_num.encode())
cur_num_hex = cur_num_md5.hexdigest()

print(cur_num_hex)
