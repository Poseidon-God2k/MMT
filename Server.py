import sys, socket

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

		udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		udpSocket.bind(('', 1026))
		udpSocket.listen(1)       

		# Receive client info (address,port) through RTSP/TCP session
		while True:
			message, clientAddress = udpSocket.recvfrom(2048)
			udpSocket.sendto(["movie.Mjpeg"].encode(), clientAddress)

			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(Server()).main()


