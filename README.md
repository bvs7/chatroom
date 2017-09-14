# ReadMe
Include documentation for course staff to run test cases.

##Implementation
###Implementation Overview
My implementation of chatroom uses a heartbeat every ~.3 seconds and two sockets for every connection between every server.
###Socket details
Servers have a listening socket on the port **25090** + id. They also have n-1 searching sockets, searching for connections on the base port **25090** + id. When each server is started, within three seconds, it will create a chatConn (chatroom connection) object that contains the socket which searched and found the other server, and the connection obtained when the other server searches and finds the socket listening on this server.
These connections are assumed to be alive when both of these connections are made, and die as soon as one of them fails. The searched sockets (now called send sockets) are lost when the recipient fails to respond in a timely fashion. (For this lab that just means the default timeout or a bad connection exception). The listened sockets (now called receive sockets) are lost when a heartbeat is not received for .8 seconds. The heartbeat is sent by every send socket once every .3 seconds.
###Message Formats
The heartbeats take the form:
`hb\n`

Messages are sent with the format:
`msg [message text]`
###Message details
When a server receives a broadcast from master, it immediately sends a `msg` to all other servers and stores the message in a list.
When a server receives a `msg` from another server, it adds the message to the list.

##Test Cases
NOTE: for some added test cases, extending the timeout time of master might be required. I use 3*60 seconds instead of 60 seconds.
NOTE: when get is called and no messages are available to report, `messages ` (notice the space after it) is returned
`hardcore` starts 16 servers and checks with three of them to see if they know all 16 are alive
`superrestart` restarts a server many times, ensuring messages are lost and that the server comes back up consistently.
`multicast` checks that waiting for one second between broadcasts from different servers ensures messages are all received in order
`multifail` checks that a process can identify up to 5 failing servers in one second
