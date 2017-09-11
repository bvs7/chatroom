#!/usr/bin/env python
# A chatroom server for lab 1


import sys
import time
from threading import Thread
from socket import socket, SOCK_STREAM, AF_INET, error as socketError, SOL_SOCKET, SO_REUSEADDR

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

class ChatroomServer:

	def __init__(self, id_, n, port):
		
		self.my_id = id_
		self.n_servers = n
		self.master_port = port
		
		self.my_port = BASE_PORT + self.my_id
		
		self.chatConns = [None]*n
		for i in range(n):
			if i == self.my_id: continue
			self.chatConns[i] = ChatConnection(i)
			
		# Create message Log
		self.msgLog = []
			
		# Start Listening and Searching Threads
		self.listenThread = Thread(target=self.listenThreadEntry)
		self.searchThread = Thread(target=self.searchThreadEntry)
		
		self.listenThread.start()
		self.searchThread.start()
		
		print "Master is port ", self.master_port
		
		# Accept master
		self.master_sock = socket(AF_INET, SOCK_STREAM)
		self.master_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.master_sock.bind( ("127.0.0.1", self.master_port) )
		self.master_sock.listen(0)
		(self.master_conn, self.master_addr) = self.master_sock.accept()
		
		self.serveMasterForever()
		
	def execMasterCmd(self,cmd):
		if "get" in cmd:
			resp = "messages " + ",".join(self.msgLog)
			self.master_conn.send(resp + "\n")
		elif "alive" in cmd:
			aliveList = []
			for c in self.chatConns:
				if c == None:
					aliveList.append(str(self.my_id))
				elif (c.inConn and c.outConn):
					aliveList.append(str(c.id_))
			resp = "alive " + ",".join(aliveList)
			self.master_conn.send(resp + "\n")
		elif "broadcast" in cmd:
			msg = cmd.split(" ",1)[1]
			self.msgLog.append(msg)
			for i in range(self.n_servers):
				if not i == self.my_id and self.chatConns[i].outConn:
					self.chatConns[i].sendSock.send("msg " + msg + "\n")
				
	def serveMasterForever(self):
		dataBuf = ""
		while True:
			recvData = self.master_conn.recv(1024)
			if recvData == 0: # Connection was closed
				self.master_conn.shutdown()
				self.master_conn.close()
				break
			dataBuf += recvData
			while "\n" in dataBuf:
				(cmd, dataBuf) = dataBuf.split("\n",1)
				print "M", self.my_id, "got", cmd
				self.execMasterCmd(cmd)
				
	def execOtherCmd(self,cmd,cc):
		if "msg" in cmd:
			self.msgLog.append(cmd.split(' ',1)[1])
			
	
	def serveOtherForever(self, chatConn_id):
		chatConn = self.chatConns[chatConn_id]
		dataBuf = ""
		while True:
			recvData = chatConn.recvConn.recv(1024)
			if recvData == 0: # Connection was closed
				chatConn.inConn = False
				chatConn.outConn = False
				break
			dataBuf += recvData
			while "\n" in dataBuf:
				(cmd, dataBuf) = dataBuf.split("\n",1)
				print self.my_id, "got", cmd
				self.execOtherCmd(cmd,chatConn)
				
	def searchThreadEntry(self):
		# Create sockets for all connections
		for i in range(self.n_servers):
			if i == self.my_id: continue
			self.chatConns[i].sendSock = socket(AF_INET, SOCK_STREAM)

		while True:
			time.sleep(0.1)
			for i in range(self.n_servers):
				chatConn = self.chatConns[i]
				if i == self.my_id: continue
				if not chatConn.outConn:
					try:
						port = chatConn.id_ + BASE_PORT
						chatConn.sendSock.connect((HOST, port))
						chatConn.sendSock.send("id "+str(self.my_id))
						chatConn.outConn = True
					except socketError:
						continue

	def listenThreadEntry(self):
		self.listen_socket = s = socket(AF_INET, SOCK_STREAM)
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		s.bind((HOST,self.my_port))
		s.listen(2)
		
		chatConns = self.chatConns
		while True:
			time.sleep(0.1)
			(conn, addr) = self.listen_socket.accept()
			other_id = int(conn.recv(1024).split()[1])
			chatConns[other_id].recvConn = conn
			chatConns[other_id].inConn = True
			handler = Thread(target=self.serveOtherForever, args=(other_id,))
			handler.start()
			self.listen_socket.listen(2)

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
		
	
