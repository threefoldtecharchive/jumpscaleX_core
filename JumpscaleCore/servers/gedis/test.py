
from Jumpscale import j
from nacl.signing import SigningKey                                                            
from secret_handshake import SHSClient                                                         
server_vk = j.data.nacl.default.verify_key.encode()                                            
client = SHSClient('localhost',8901,SigningKey.generate(),server_vk) 
j.shell()
