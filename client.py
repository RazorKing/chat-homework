#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO 聊天记录保存
# TODO 账号密码
# TODO 加密传输
# TODO 表情
# TODO 语音播放
# TODO 文件直接打开

import wx
import time
import sys
import threading
import os
import socket

# 规定时间输出格式
ISOTIMEFORMAT="%Y-%m-%d %X"
# 定义全局变量 方便修改host与端口
PORT = 3188
HOST = "192.168.0.100"

# 文件保存地址 默认为项目目录下recvfile文件夹内
FILE_RECV_DIR="recvfile/"

# 用于客户端给服务器发送信息时的处理
def addCMD(cmd,msg):
    s = cmd + "&&"
    if type(msg)==type([]):
        for m in msg:
            s += (m + "&&")
    else:
        s += msg+"&&"
    s = s.strip("&")
    return s

# 总框架类 继承自wx库中Frame框架类
class ListFrame(wx.Frame):
    def __init__(self, parent, id, username):
        wx.Frame.__init__(self, parent, id, "ChatClient", size=(700, 500))

        # 接收自服务器的命令头对应的执行函数，用字典操作
        self.cmdDict = {
            "getmember":self.cmd_initList,
            "adduser":self.cmd_addUser,
            "deluser":self.cmd_delUser,
            "talkfrom":self.cmd_talkFrom,
            "filefrom":self.cmd_fileFrom,
            "filestart":self.cmd_fileStart,
            "fileend":self.cmd_fileEnd
        }
        self.panel = wx.Panel(self, -1)
        self.statusbar = self.CreateStatusBar()

        # username 用户名
        self.username = username
        self.StaticText = wx.StaticText(self.panel,-1,"Name : "+self.username, (10, 10), (180, -1), wx.ALIGN_CENTER)
        self.StaticText.SetForegroundColour("White")
        self.StaticText.SetBackgroundColour("Grey")
        font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        self.StaticText.SetFont(font)

        # 用户列表
        self.list = listText(self.panel,self.username)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onClickon)
        self.Show()

        # 对话框
        self.NowPanel = None
        self.MsgDict = {}

        self.getMember()

        self.Bind(wx.EVT_CLOSE,self.OnClose)

        # 监听socket则开启新线程
        recvThread = threading.Thread(target=self.loopListen, args=())
        recvThread.setDaemon(True)
        recvThread.start()


    def loopListen(self):
        while 1 :
            data = s.recv(1024)
            print "getdata",data
            if not data :
                print '\nDisconnected from chat server'
            else:
                da = data.split("&&")
                self.cmdDict.get(da[0])(da)


    # 相应服务器发来信息的指令

    # 初始化列表
    def cmd_initList(self,da):
        self.list.InitialList(da[1:])

    # 添加新在线成员
    def cmd_addUser(self,da):
        self.list.addUser(da[1])

    # 删除离线成员
    def cmd_delUser(self,da):
        self.list.delUser(da[1])

    # 接收来自他人的信息
    def cmd_talkFrom(self,da):
        self.processMsg(da,"At "+da[3]+":\n\t<"+da[1]+" Said>:", da[2]+"\n")

    # 开始接收信息
    def cmd_fileStart(self,da):
        self.processMsg(da,"At "+da[3]+":\n\t<"+da[1]+" Send File>:", da[2]+" Please stop sending message!\n")

    # 结束接收信息
    def cmd_fileEnd(self,da):
        self.processMsg(da,"At "+da[3]+":\n\t<"+da[1]+" End Sending File>:", da[2]+" You can start sending now!\n")

    # 在对话框中打印信息
    def processMsg(self,da,formsg,msg):
        if self.NowPanel!=None and self.NowPanel.name==da[1]:
            self.NowPanel.DisplayText.SetDefaultStyle(wx.TextAttr("blue"))
            self.NowPanel.DisplayText.AppendText(formsg)
            self.NowPanel.DisplayText.SetDefaultStyle(wx.TextAttr("black"))
            self.NowPanel.DisplayText.AppendText(msg)
        else:
            self.gotMsg(da[1])
            if da[1] not in self.MsgDict.keys():
                self.MsgDict[da[1]] = []
                self.MsgDict[da[1]].append([formsg, msg])
            else:
                self.MsgDict[da[1]].append([formsg, msg])

    # 接收文件
    def cmd_fileFrom(self,da):
        if os.path.exists(FILE_RECV_DIR+self.username) and os.path.isdir(FILE_RECV_DIR+self.username):
            pass
        else:
            os.makedirs(FILE_RECV_DIR+self.username)
        f = open(FILE_RECV_DIR+self.username+"/"+da[2] , 'ab')
        f.write(da[3])
        f.close()

    # 请求获得用户列表
    def getMember(self):
        ms = addCMD("getmember",[])
        s.send(ms)

    # 点击某在线用户
    def onClickon(self, evt):
        index = self.list.GetFirstSelected()
        name = evt.GetItem().GetText()
        while index != -1:
            self.list.SetItemTextColour(index, (0,0,0))
            index = self.list.GetNextSelected(index)
        if name in self.MsgDict.keys():
            mList = self.MsgDict[name]
        else:
            mList = []
        self.NowPanel = chatPanel(self.panel,name,mList)
        self.NowPanel.Show()

        self.NowPanel.sendButton.Bind(wx.EVT_BUTTON,self.onSend)
        self.NowPanel.fileButton.Bind(wx.EVT_BUTTON,self.onSendFile)

    # 点击Send按钮发送消息
    def onSend(self,e):
        msg = self.NowPanel.InputText.GetLineText(0)
        ntime = time.strftime( ISOTIMEFORMAT, time.localtime())

        self.NowPanel.DisplayText.SetDefaultStyle(wx.TextAttr((0,154,0)))

        self.NowPanel.DisplayText.AppendText("At "+ntime+":\n\t<You Said>:")
        self.NowPanel.DisplayText.SetDefaultStyle(wx.TextAttr("black"))
        self.NowPanel.DisplayText.AppendText(msg+"\n")
        self.NowPanel.InputText.SetValue("")
        s.send("talkto&&"+self.NowPanel.name+"&&"+msg+"&&"+self.username+"&&"+ntime)

    # 发送文件
    def onSendFile(self,e):
        dialog = wx.FileDialog(self,"Open file...",os.getcwd(),style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            name = dialog.GetFilename()
            try:
                fd = open(filename, 'rb')
                s.send("filestart&&"+self.NowPanel.name+"&&"+self.username+"&&"+name+"&&"+time.strftime( ISOTIMEFORMAT, time.localtime()))
                self.NowPanel.DisplayText.AppendText("At "+time.strftime( ISOTIMEFORMAT, time.localtime())+":\n\t<You Send File>:"+name+" Please stop sending message!\n")
                time.sleep(0.1)
                # 分段传输
                while True:
                    data = fd.read(80)
                    if not data:
                        break
                    s.send("fileto&&"+self.NowPanel.name+"&&"+self.username+"&&"+name+"&&"+data)
                    time.sleep(0.1)
                s.send("fileend&&"+self.NowPanel.name+"&&"+self.username+"&&"+name+"&&"+time.strftime( ISOTIMEFORMAT, time.localtime()))
                self.NowPanel.DisplayText.AppendText("At "+time.strftime( ISOTIMEFORMAT, time.localtime())+":\n\t<You End Sending File>:"+name+" You can start sending now!\n")
                fd.close()
            except:
                wx.MessageBox("%s is not a match file." %filename,"oops!",style=wx.OK|wx.ICON_EXCLAMATION)
        # 销毁对话框,释放资源.
        dialog.Destroy()

    # 接收到消息，对应姓名变为红色
    def gotMsg(self,name):
        index = self.list.FindItem(-1,name)
        while index != -1:
            self.list.SetItemTextColour(index, (255,0,0))
            index = self.list.GetNextSelected(index)

    # 关闭
    def OnClose(self, evt):
        sys.exit()
        evt.Skip()


# 定义聊天框panel类
class chatPanel(wx.Panel):
    def __init__(self,parent,name,msgList):
        wx.Panel.__init__(self, parent, -1,
                          (200,10),(450, 450))
        self.DisplayText = wx.TextCtrl(self, -1, '',(0,50),
                                       size=(450, 300), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
        for ll in msgList:
            self.DisplayText.SetDefaultStyle(wx.TextAttr("blue"))
            self.DisplayText.AppendText(ll[0])
            self.DisplayText.SetDefaultStyle(wx.TextAttr("black"))
            self.DisplayText.AppendText(ll[1])

        self.name = name
        self.StaticText = wx.StaticText(self, -1, "Talking to :" + name)
        self.StaticText.SetForegroundColour("White")
        self.StaticText.SetBackgroundColour("Grey")
        font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        self.StaticText.SetFont(font)

        self.InputText = wx.TextCtrl(self, -1,'',
                                     pos=(0, 371), size=(290, -1))

        self.sendButton = wx.Button(self, -1, "Send", pos=(290, 368))
        self.sendButton.SetDefault()

        self.fileButton = wx.Button(self, -1, "File", pos=(375, 368))



# 定义好友列表statictextpanel类
class listText(wx.ListCtrl):
    def __init__(self,parent,username):
        #构造ListCtrl
        wx.ListCtrl.__init__(self,parent,-1,(10, 60), (180, 350), style=wx.LC_REPORT)
        self.listDict = {}
        self.name = username

    def InitialList(self, n_list):
        self.InsertColumn(0, "List of online user")
        self.SetColumnWidth(0,180)
        self.SetBackgroundColour((230,230,230))
        for col, name in enumerate(n_list):
            if name != self.name:
                self.InsertStringItem(col, name)
                self.listDict[col] = name
        print self.listDict;


    def addUser(self,name):
        i = 1
        found = 0
        while not found:
            if i in self.listDict.keys():
                i = i + 1
            else :
                found = 1
        self.InsertStringItem(i,name)
        self.listDict[i] = name

    def delUser(self,name):
        for key,value in self.listDict.items():
            if value == name:
                self.DeleteItem(self.FindItem(-1,name))
                del self.listDict[key]

    def gotMsg(self,name):
        self.FindItem(name).gotMsg()




# 用于检验用户名在服务器端是否存在
def loginInput(soc):
    #input username
    data = "alreadyexist"
    username = ""
    while(data=="alreadyexist"):
        dlg = wx.TextEntryDialog(None, "Please enter the user name:", 'Login for chat client', 'username')
        if dlg.ShowModal() == wx.ID_OK:
            username = dlg.GetValue()
            print "login&&"+username
            soc.send("login&&"+username)
            data = soc.recv(1024)
            if(data=="alreadyexist"):
                msgdlg = wx.MessageDialog(None,"The name is already exist,please change one!","Warning of rename")
                msgdlg.ShowModal()
        else:
            wx.Exit()
    return username


if __name__ == '__main__':
    #建立socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try :
        s.connect((HOST, PORT))
    except :
        print 'Unable to connect'
        sys.exit()

    app = wx.App(False)
    username = loginInput(s)

    #list
    frame = ListFrame(None,-1, username)
    app.MainLoop()
