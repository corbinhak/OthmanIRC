# -*- coding: utf-8 -*-

import socket
from threading import Thread
from appJar import gui
import random

serverName = ''
serverPort = ''
nickname = ''
autojoin = ''
password = ''
my_msg = ''
last_msg = ''
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def press(button):
    if button == "Connect":
        global serverName
        global serverPort
        global nickname
        global autojoin
        global password
        serverName = app.getEntry("Server")
        serverPort = app.getEntry("Port")
        nickname = app.getEntry("Nickname")
        autojoin = app.getEntry("Autojoin")
        password = app.getEntry("Password")
        if not serverName:
            serverName = '127.0.0.1'
        if not serverPort:
            serverport = 6667
        if not nickname:
            nickname = 'Guest' + str(random.randint(1000,9999))
        if not serverName:
            app.errorBox("noServer", "No server IP was given.")
        else:
            if connect():
                app.hideSubWindow("Connect")
                app.show()
    else:
        app.stop()
        clientSocket.close()

def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = clientSocket.recv(1024).decode("utf8")

            if msg.startswith("/msg"):
                command,user,message = msg.split("&&")
                app.addListItem("MessageList", "<"+user+" --> " + nickname + "> " + message)
                global last_msg
                last_msg = user
                """/msg&&fromuser&&message"""
            elif msg.startswith("/ping"):
                app.addListItem("MessageList", "Pong!")
            else:
                msgChannel, msgUser, msgData = msg.split("&&")
                app.addListItem("MessageList", msgUser+": "+msgData)

        except OSError:
            break


def send(event=None):  # event is passed by binders.
    """Handles sending of messages."""
    channel = "#general"
    msg = channel+"&&" +app.getEntry("Entry")
    if msg.startswith("/quit"):
        clientSocket.close()
        app.quit()
        return
    elif msg.startswith("/msg"):
        command,user,message=msg.split("&&")
        app.addListItem("MessageList", "<" + nickname + " --> " + user + "> " + message)
        msg = command+"&&"+user+"&&"+message
    elif msg.startswith("/reply"):
        command,message = msg.split("&&")
        app.addListItem("MessageList", "<" + nickname + " --> " + last_msg + "> " + message)
        msg = command + "&&" + message
    else:
        channelMsg, msgBody = msg.split("&&")
        app.addListItem("MessageList", nickname+": " + msgBody)

    try:
        clientSocket.send(msg.encode())
    except:
        app.errorBox("Could not send message.")

    app.setEntry("Entry", "")



def on_closing(event=None):
    """This function is to be called when the window is closed."""
    app.stop()
    clientSocket.close()

def connect():
    global nickname
    try:
        clientSocket.connect((serverName, int(serverPort)))
    except:
        return False
    initMessage = password + "&&" + nickname + '&&' + autojoin
    clientSocket.send(initMessage.encode())
    handshake = clientSocket.recv(1024).decode()
    newNickname,channel = handshake.split("&&")
    nickname = newNickname
    if not handshake:
        app.errorBox("Could not connect.")
        return False
    receive_thread = Thread(target=receive)
    receive_thread.start()
    return True

app = gui("OthmanIRC 0.02")
app.icon = "icon.gif"
app.startTabbedFrame("Channels")
app.startTab("Server")
app.addListBox("MessageList")
app.addLabelEntry("Entry").bind("<Return>", send)
app.setEntryDefault("Entry","Enter message here.")
app.addButton("Send", send)
app.stopTab()
app.stopTabbedFrame()

app.startSubWindow("Connect")
app.addLabelEntry("Server")
app.addLabelEntry("Port")
app.addLabelSecretEntry("Password")
app.addLabelEntry("Nickname")
app.addLabelEntry("Autojoin")
app.setEntryDefault("Server", "127.0.0.1")
app.setEntryDefault("Nickname", "guest")
app.setEntryDefault("Port", "6667")
app.addButtons(["Connect", "Cancel"], press)
app.stopSubWindow()

app.go(startWindow="Connect")
