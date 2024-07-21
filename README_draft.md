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
### Prerequisties
- Python 3.9 or above

### Setup environment
#### Windows user
In the project root directory, run the following command in cmd to setup the environment:
```cmd
.\win_venv\Scripts\activate
```

To deactivate the environment:
```cmd
.\win_venv\Scripts\deactivate
```

In the case of permission issues, try the following command:
```cmd
python -m venv my_venv
.\my_venv\Scripts\activate
```
```cmd
.\my_venv\Scripts\deactivate
```

#### Mac or Linux user
In the project root directory, run the following command in bash to setup the environment:
```bash
source .\unix_venv\Scripts\activate
```

In the case of permission issues, try the following command:
```cmd
python -m venv my_venv
.\my_venv\Scripts\activate
```

To deactivate the environment:
```bash
deactivate
```
### Installing
Here is a list of dependencies for the project:
```
aiofiles==24.1.0
cryptography==42.0.8
PyYAML==6.0.1
websockets==12.0
pytest==8.3.1
```

After activating environment, install requirements with `pip`:
```
pip install -r requirements.txt
```

User can now start running the chat system

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

##### 1.2 Create New Account in Server [server/register.py]
**Make sure you are in the `./server/` directory**

```bash
cd server
```

Inside the `./server/` directory, run the following command to start a registration process:
```
python register.py
```

The existing account for testing:

passwords for c1 - c5:
1. potato
2. watermelon
3. banana
4. coconut
5. apple


##### 1.3 Set Up the Client Configuration [client/client_config.yaml]
```
chat_server
host: <chat_server_ip>
port: <chat_server_port>
```
### 2. Start the Chat System
##### 2.1 Start the Server
Open a new terminal

**Make sure you are in the `./server/` directory**

```bash
cd server
```

Command to start the chat server:
```
python secure_chatapp.py
```
![Alt Text](snapshot/server_start.png)<img width="100">

##### 2.2 Start the Client:
Open a new terminal

**Make sure you are in the `./server/` directory**

```bash
cd client
```

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
