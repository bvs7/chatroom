#!/usr/bin/env python
# A chatroom server for lab 1


import sys
import time
from threading import Thread
from socket import socket, SOCK_STREAM, AF_INET, error as socketError, SOL_SOCKET, SO_REUSEADDR

HOST = "127.0.0.1"
BASE_PORT = 25090

HB_PERIOD = 0.3
TO_PERIOD = 0.8

# A list of these are updated by the Search and Listen threads?
class ChatConnection:
	def __init__(self, id_):
		self.id_ = id_
		self.recvConn=None
		self.sendSock=None
		self.inConn=False  #Listened and got incoming connection
		self.outConn=False #Searched and got outgoing connection
		
		self.lastHB = time.time()

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
		self.listenThread = Thread(target=self.listenThreadEntry, name=("listener"+str(self.my_id)))
		self.searchThread = Thread(target=self.searchThreadEntry, name=("searcher"+str(self.my_id)))
		self.hbThread     = Thread(target=self.heartbeatThreadEntry, name=("heartbeat"+str(self.my_id)))
		
		self.listenThread.start()
		self.searchThread.start()
		self.hbThread.start()
		
		#print "Master is port ", self.master_port
		
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
				self.master_conn.close()
				break
			dataBuf += recvData
			while "\n" in dataBuf:
				(cmd, dataBuf) = dataBuf.split("\n",1)
				#print "M", self.my_id, "got", cmd
				self.execMasterCmd(cmd)
				
	def execOtherCmd(self,cmd,cc):
		if "msg" in cmd:
			self.msgLog.append(cmd.split(' ',1)[1])
			cc.lastHB = time.time()
		if "hb" in cmd:
			cc.lastHB = time.time()
			#print "HB update", self.my_id, cc.id_
			
	
	def serveOtherForever(self, conn):
		dataBuf = ""
		other_id = -1
		while other_id == -1:
			dataBuf = conn.recv(1024)
			if "\n" in dataBuf:
				(cmd, dataBuf) = dataBuf.split("\n",1)
				if "id" in cmd:
					other_id = int(cmd.split()[1])
		chatConn = self.chatConns[other_id]
		chatConn.recvConn = conn
		chatConn.inConn = True
		chatConn.lastHB = time.time()
		
		timeout = Thread(target=self.timeoutThreadEntry, args=(chatConn,))
		timeout.start()
		
		while True:
			recvData = chatConn.recvConn.recv(1024)
			if recvData == 0: # Connection was closed
				break
			dataBuf += recvData
			while "\n" in dataBuf:
				(cmd, dataBuf) = dataBuf.split("\n",1)
				self.execOtherCmd(cmd,chatConn)
				
	def searchThreadEntry(self):
		# Create sockets for all connections
		for i in range(self.n_servers):
			if i == self.my_id: continue
			self.chatConns[i].sendSock = socket(AF_INET, SOCK_STREAM)

		while True:
			time.sleep(0.01)
			for i in range(self.n_servers):
				chatConn = self.chatConns[i]
				if i == self.my_id: continue
				if not chatConn.outConn:
					try:
						port = chatConn.id_ + BASE_PORT
						chatConn.sendSock.connect((HOST, port))
						chatConn.sendSock.send("id "+str(self.my_id)+"\n")
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
			time.sleep(0.01)
			(conn, addr) = self.listen_socket.accept()
			handler = Thread(target=self.serveOtherForever, args=(conn,))
			handler.start()
			self.listen_socket.listen(2)
			
	def heartbeatThreadEntry(self):
		while True:
			time.sleep(HB_PERIOD)
			for i in range(self.n_servers):
				if i == self.my_id:
					continue
				if self.chatConns[i].outConn:
					try:
						self.chatConns[i].sendSock.send("hb\n")
					except Exception as e:
						#print e
						self.chatConns[i].outConn = False
						self.chatConns[i].sendSock = socket(AF_INET, SOCK_STREAM)
						
						
	def timeoutThreadEntry(self, chatConn):
		while chatConn.inConn:
			time.sleep(0.1)
			if time.time() - chatConn.lastHB > TO_PERIOD:
				#print "TIMED OUT", self.my_id, chatConn.id_
				chatConn.inConn = False
				
			

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
		
	
