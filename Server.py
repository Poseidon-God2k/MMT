import sys, socket
from os import listdir
from os.path import isfile, join

from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		try:
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		rtspSocket.bind(('', SERVER_PORT))
		rtspSocket.listen(5)   
		fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		fileSocket.bind(('', 12345))
		fileSocket.listen(1)
		n = 0
		# Receive client info (address,port) through RTSP/TCP session
		while True:

			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			clientInfo['fileSocket'] = fileSocket.accept()
			# if n == 0:
			# 	msg = clientInfo['rtspSocket'][0].recv(256).decode()
			# if msg == "Hello":
			# 	path = "D:/HK201/Networking/Assignment1_extend/video"
			# 	clientInfo['rtspSocket'][0].send(" ".join(listdir(path)).encode())
			# else:
			ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(Server()).main()


