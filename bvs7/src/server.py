#!/usr/bin/env python
# A chatroom server for lab 1


import sys
from threading import Thread
from socket import socket, SOCK_STREAM, AF_INET

HOST = "127.0.0.1"
BASE_PORT = 25090

# A list of these are updated by the Search and Listen threads?
class ChatConnection:
	def __init__(self, id_):
		self.id_ = id_
		self.recvConn=None
		self.sendSock=None
		self.inConn=False  #Listened and got incoming connection
		self.outConn=False #Searched and got outgoing connection

# Thread to open connections with any other servers
class SearchThread(Thread):
	def __inif__(self, cs):
		self.cs = cs
		
		# Create sockets for all connections
		for i in range(self.cs.n_servers):
			if i == self.cs.my_id: continue
			self.cs.chatConns[i].sendSock = socket(AF_INET, SOCK_STREAM)			
		
	def run(self):
		while True:
			for i in range(self.cs.n_servers):
				chatConn = self.cs.chatConns[i]
				if i == self.cs.my_id: continue
				if not chatConn.outConn:
					try:
						chatConn.sendSock.connect((HOST, chatConn.id_ + BASE_PORT))
					except socket.error:
						continue
					chatConn.outConn = True
						
# Thread to listen for connections from any servers
class ListenThread(Thread):
	def __init__(self, cs):
		self.cs = cs
		self.listen_socket = socket(AF_INET, SOCK_STREAM)
		self.bind((HOST,self.cs.my_port))
		self.listen(2)
		
	def run(self):
		chatConns = self.cs.chatConns
		while True:
			(conn, addr) = s.accept()
			other_id = int(addr[1]) - BASE_PORT
			chatConns[other_id].recvConn = connect
			chatConns[other_id].outConn = True

class ChatroomServer:

	def __init__(self, id_, n, port):
		
		self.my_id = id_
		self.n_servers = n
		self.master_port = port
		
		self.my_port = BASE_PORT + self.my_id
		
		self.chatConns = [None]*n
		for i in range(n):
			if i = self.my_id: continue
			self.chatConns[i] = ChatConnection(BASE_PORT+i)
			
		# Create message Log
		self.msgLog = []
			
		# Start Listening and Searching Threads
		self.listenThread = ListenThread(self)
		self.searchThread = SearchThread(self)
		
		self.listenThread.start()
		self.searchThread.start()
		
		# Accept master
		self.master_sock = socket(AF_INET, SOCK_STREAM)
		self.master_sock.bind( ("127.0.0.1", self.master_port) )
		self.master_sock.listen(0)
		(self.master_conn, self.master_addr) = self.master_sock.accept()
		
	def execMasterCmd(cmd):
		if "get" in cmd:
			resp = "messages " + msgLog.join(",")
			self.master_conn.send(resp)
		elif "alive" in cmd:
			resp = "alive " + [str(c.id_) for c in self.chatConns if (not c == None and c.inConn and c.outConn].join(",")
			self.master_conn.send(resp)
				
	def serveMasterForever(self):
		dataBuf = ""
		while True:
			recvData = self.master_conn.recv(1024)
			if recvData == 0: # Connection was closed
				break
			dataBuf += recvData
			while "\n" in dataBuff:
				(cmd, dataBuff) = dataBuff.split("\n",1)
				self.execMasterCmd(cmd)
			
		
	


if __name__ == "__main__":
	
	# Check for correct arguments
	if len(sys.argv) < 4:
		print "Too few arguments for server.py\nUsage: \npython server.py <id> <n> <port>"
		exit(1)

	try:
		server_id = int(sys.argv[1])
		server_n = int(sys.argv[2])
		server_port = int(sys.argv[3])
	except ValueError as e:
		print "<id>, <n>, and <port> must be ints"
		exit(1)
		
	cs = ChatroomServer(server_id, server_n, server_port)
		
	
