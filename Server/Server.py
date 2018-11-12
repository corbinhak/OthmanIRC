import _thread
import socket  # get socket constructor and constants

myHost = ''  # server machine, '' means local host
myPort = 6667  # listen on a non-reserved port number
version = '0.0.1'

# clients[connection] = client
clients = {}
# channels[channelName] = channel
channels = {}
# claimedusernames = [name1, name2, name3]
claimedusernames = []

sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockobj.bind((myHost, myPort))
sockobj.listen(10)


# channel class, Name and Password for Channel
# If password = ' ' a password is not required to join the server
# handles what users are in the channel and the channel infomation
class channel:

    def __init__(self, name, password=' '):
        self.name = name
        self.password = password
        self.ispublic = False
        if password == ' ':
            self.ispublic = True
        self.connectedclients = {}
        channels[name] = self


# client class
# handles user data and connection
class client:

    def __init__(self, connection, username, autojoin="#general", password=' '):
        clients[connection] = self
        self.connection = connection
        self.password = password
        self.username = get_username(username)
        self.lastmsgfrom = self
        claimedusernames.append(self.username)
        # List of Channels the Client is in, contains names of the channel
        self.channelsin = []
        print(client_connect_channel("#general", connection))
        if autojoin != "#general":
            client_connect_channel(autojoin, connection, password)

    def strchannelsin(self):
        c = ""
        for x in self.channelsin:
            c = c + x + " "
        return c


# Connects client to the channel if the password is correct or the server password is ' '
# Adds client to connectedclients
# Adds channel to client.channelsin
def client_connect_channel(channelname, connection, password=' '):
    connectingclient = clients[connection]
    if channelname in channels:
        if channels[channelname].password == password or channels[channelname].password == ' ':
            channels[channelname].connectedclients[connection] = connectingclient
            connectingclient.channelsin.append(channelname)
            announce_connected_client(connection, channelname)
            return True
    return False


# removes client from specified channel
def client_remove_channel(channelname, client):
    clients[client].channelsin.remove(channelname)
    channels[channelname].connectedclients.pop(client)


def announce_connected_client(connection, channelname):
    message = str(channelname + "&&" + "Server&&" + clients[connection].username + " has connected to " + channelname)
    for c in channels[channelname].connectedclients:
        if c != connection:
            c.send(message.encode())


# creates client when it first connects
# data should be in format password:username:autojoin
def clientFirstConnect(connection, data):
    password, username, autojoin = data.split("&&")
    client(connection, username, autojoin, password)


# returns an available nickname
# if nickname is taken will use get_nickname_num if name is taken and append a number to end of nickname
def get_username(username):
    if username in claimedusernames and username != "Server":
        username = get_username_num(username, 1)
    return username


# used with get_username
def get_username_num(username, num):
    name = username + str(num)
    if name in claimedusernames:
        return get_username_num(username, num + 1)
    return name


# return true if user is in channel, false if otherwise
def user_in_channel(connection, channelname):
    return channelname in clients[connection].channelsin


# sends message to all clients in channel from user with time stamp
def server_send_channelmessage(channelname, user, data):
    message = str(channelname + "&&" + user + "&&" + data)
    for connection in clients:
        client = clients[connection]
        if client.username != user:
            connection.send(message.encode())


"""Commands from Client"""


# adds user to channel in data, if channel has a password it should be in data.
# returns true if successful, false otherwise
def join(connection, data):
    try:
        data, password = data.split("&&")
        return client_connect_channel(data, connection, password)
    except ValueError:
        return client_connect_channel(data, connection)


# Sends a msg from connection to user containing message, contained in data
# Returns true if successfully send, false is otherwise
def msg(connection, data):
    try:
        user, message = data.split("&&")
        message = str(clients[connection].username) + "&&" + message
        for x in clients:
            if x.username == user:
                x.send(message.encode())
                x.lastmsgfrom = connection
                return True
    except:
        return False
    return False


def reply(connection, data):
    try:
        if clients[connection].lastmsgfrom in clients:
            clients[connection].lastmsgfrom.send(data.encode())
            return True
    except:
        return False
    return False


def ping(connection):
    print("ping from" + clients[connection].username)
    connection.send("pong".encode())


"""End Commands from Client"""


def clientremoved(connection, error="unknown reason"):
    print(str(clients[connection].username) + " removed from server because " + str(error))


def handleClient(connection):
    clientFirstConnect(connection, connection.recv(1024).decode())
    thisclient = clients[connection]
    connection.send((str(thisclient.username) + "&&" + thisclient.strchannelsin()).encode())
    print(str(thisclient.username) + "&&" + str(thisclient.strchannelsin()))

    while True:
        try:
            data = connection.recv(1024).decode()
            print("Received from " + thisclient.username + ":" + data)
            header, data = data.split("&&")
            # Checks and uses command from Client
            if header[:1] == '/':
                if header == "/quit":
                    clientremoved(connection, "closed by client")
                    break
                elif header == "/join":
                    connection.send(str(join(connection, data).encode()))
                elif header == "/msg":
                    connection.send(str(msg(connection, data).encode()))
                elif header == "/reply":
                    connection.send(str(reply(connection, data).encode()))
                elif header == "/ping":
                    ping(connection)
                else:
                    connection.send(str(header + " is unknown command").encode())
            # Checks and sends message to channel
            elif header[:1] == '#':
                if header in thisclient.channelsin:
                    server_send_channelmessage(header, thisclient.username, data)
                else:
                    connection.send(str(header + " is an unknown channel").encode())
            else:
                connection.send("Unknown Message Format".encode())
        except ConnectionResetError:
            clientremoved(connection, "connection was forcibly closed by the client")
            break
        except ValueError:
            connection.send("Unknown Message Format".encode())
            continue

    connection.close()


def dispatcher():  # listen until process killed
    while True:  # wait for next connection
        connection, address = sockobj.accept()  # pass to thread for service
        _thread.start_new(handleClient, (connection,))


generalChannel = channel("#general", ' ')
hiddenChannel = channel("#seceret", "1234")
dispatcher()
