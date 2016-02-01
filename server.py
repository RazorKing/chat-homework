#!/usr/bin/env python
# -*-coding:utf-8-*-
from socket import *
import select

HOST = "127.0.0.1"
PORT = 3188

class Server():
    def __init__(self, host, port):
        self.CONNECTION_LIST = []  # existing socket of server
        self.port = port
        self.host = host

        #用户字典，key为用户名，value为对应的socket
        self.userDict = {}

        #命令字典，响应来自客户端的命令头
        self.cmdDict={'login': self.cmd_login,
                      'getmember': self.cmd_getMember,
                      'talkto':self.cmd_talkTo,
                      'fileto':self.cmd_sendFile,
                      'filestart':self.cmd_fileStart,
                      'fileend':self.cmd_fileEnd
                      }
        #建立socket
        #TODO 建立传送文件的新的端口
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((self.host,self.port))
        self.socket.listen(10)
        # select readable list add main socket
        self.CONNECTION_LIST.append(self.socket)
        print "Server created on %s:%d" %(self.host,self.port)

    #利用select库实现循环监听各个socket
    def start(self):
        while 1:
            self.read,self.write,self.error = select.select(self.CONNECTION_LIST,[],[])
            for socket in self.read:
                if socket == self.socket:
                    sockfd, addr = self.socket.accept()
                    self.CONNECTION_LIST.append(sockfd)
                    print "Client (%s, %s) connected" % addr
                else:
                    try:
                        data = socket.recv(1024)
                        print "getdata:"+data+" from "+ "(%s,%s)" %addr
                        if data:
                            da = data.split("&&")
                            try:
                                #根据da[0]命令选择对应执行函数
                                self.cmdDict.get(da[0])(da,socket)
                            except:
                                print data
                                print "error get cmd"
                                print error
                    except:
                        self.logout(addr,socket)
                        continue


    #对应客户端登录请求，广播刷新成员列表
    def cmd_login(self,da,soc):
        name = da[1]
        if name in self.userDict.keys():
            report_send(soc, "alreadyexist")
        else:
            report_send(soc,str(1))
            self.userDict[da[1]] = soc
            for na in self.userDict.keys():
                if na == name:
                    pass
                else:
                    report_send(self.userDict[na], "adduser&&"+name)

    #普通信息
    def cmd_talkTo(self,da,sock):
        otsock = self.userDict[da[1]]
        report_send(otsock,"talkfrom&&"+da[3]+"&&"+da[2]+"&&"+da[4])

    #相应第一次初始化列表时的请求
    def cmd_getMember(self,da,sock):
        # generate msg
        msg = 'getmember&&'
        for name in self.userDict.keys():
            msg+=(name + "&&")
        msg = msg.strip("&&")
        report_send(sock,msg)

    #相应发送文件请求
    def cmd_sendFile(self,da,sock):
        otsock = self.userDict[da[1]]
        report_send(otsock,"filefrom&&"+da[2]+"&&"+da[3]+"&&"+da[4])
        #filefrom + sendFromName + filename + data

    #相应文件开始发送请求
    def cmd_fileStart(self,da,sock):
        otsock = self.userDict[da[1]]
        report_send(otsock,"filestart&&"+da[2]+"&&"+da[3]+"&&"+da[4])
        #filefrom + sendFromName + filename + time

    #相应文件结束发送请求
    def cmd_fileEnd(self,da,sock):
        otsock = self.userDict[da[1]]
        report_send(otsock,"fileend&&"+da[2]+"&&"+da[3]+"&&"+da[4])
        #fileend + sendtoname + filename + time

    #相应登出，处理socket关闭，以及服务器清除工作
    def logout(self,addr,socket):
        name = ""
        for key,value in self.userDict.items():
            if value == socket:
                name = key
                del self.userDict[key]
        socket.close()
        self.CONNECTION_LIST.remove(socket)
        print "%s,%s is offline" %(addr,name)
        for na in self.userDict.keys():
            report_send(self.userDict[na], "deluser&&"+ name)


# 所有的发送均通过此函数并打印在终端
def report_send(sock,msg):
    addr = sock.getpeername()
    print "send the msg:"+ msg + "to",addr
    sock.send(msg)


if __name__ == '__main__':
    server = Server(HOST,PORT)
    server.start()