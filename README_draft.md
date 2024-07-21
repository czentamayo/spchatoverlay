# Secure Programming Project 2024
##### Group Number: 4
##### Group Member: Anlan Zou, Czennen Trixter Tamayo, Yan Lok Chan, Yu-Ting Huang

## Description
<!-- A brief description of what the project is, what it does, and why it is useful. -->
A light weight Command Line Interface chat system based on Python and WebSocket.
Features include:
1. Private text messaging
2. Group messaging
3. File transfer
4. End-to-end encryption

## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Testing and Interoperability](#testing-and-interoperability)


## Installation
Step-by-step instructions on how to install and set up the project.

### Prerequisites
List any software or tools needed before installing.

### Installing
1. Step 1
2. Step 2
3. Step 3

## Usage
### 1. Server and Client Configuration
##### 1.1 Set Up the Server Configuration [server/server_config.yaml]
```
server_name: s1
chat_server:
  host: <local_ip>
  port: <port_number>
exchange_server:
  host: <local_ip>
  port: <port_number>
remote_servers:
  - name: <name_of_server>
    host: <remote_server_ip>
    port: <remote_server_port>
# More remote server settings
#  - name: <name_of_server>
#    host: <ip_addr_of_remote_server>
#    port: <port_intergroup_chat>
```
##### 1.2 Set Up the Client Configuration [client/client_config.yaml]
```
chat_server
host: <chat_server_ip>
port: <chat_server_port>
```
### 2. Start the Chat System
##### 2.1 Start the Server
Open a new terminal
**Make sure you are in the `server/` directory**
Command to start the chat server:
```
cd server
python secure_chatapp.py
```
![Alt Text](snapshot/server_start.png)<img width="100">

##### 2.2 Start the Client:
Open a new terminal
**Make sure you are in the `client/` directory**
Command to start the chat client:
```
cd client
python chat_client.py
```
![Alt Text](snapshot/client_start.png)<img width="100">

### 3. Log in
```
# Example
Enter your username:
c1
Enter your password:
potato
```
If login successfully, the following message will display:
```
Authentication successful!
active users: ['c1(c1@s2)]
```
![Alt Text](snapshot/client_auth.png)<img width="100">

### 4. Check Online Users
Format: LIST
```
LIST
```
![Alt Text](snapshot/client_list.png)<img width="100">

### 5. Messaging
##### 5.1 Private Message
Format: @receipient@servername message
```
# Example
@C2@S2 hello
```
![Alt Text](snapshot/client_msg_rcv.png)<img width="100">

##### 5.2 Group Message
Directly input the message
```
# Example:
Hi everyone
```
![Alt Text](snapshot/client_msg_broadcast.png)<img width="100">

### 5. File Transfer
Format: FILE receipient@servername filename
```
# Example
FILE C2@S2 readme.md
```

### 6. Exit the Chatroom
```
EXIT
```

## Testing and Interoperability
### 1. Test Plan
![Alt Text](snapshot/test_sheet.jpeg)<img width="100">

### 2. Regression Test
Regression Test can be run within the corresponding server/client directory

#### Server `./server/`
```python
python -m pytest -v ./test_server.py

```

#### Client `./client/`
```python
python -m pytest -v ./test_client.py

```

### 3. Test Group Information  
Group 1  
?Group 3  
Group 8  
Group 11  
?Group 13  
