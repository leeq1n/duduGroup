import json
import os

import requests
from flask import Flask, request
from time import sleep
import threading

from main import *

class Logger:
    def __init__(self, level='debug'):
        self.level = level

    def DebugLog(self, *args):
        if self.level == 'debug':
            print(*args)

    def TraceLog(self, *args):
        if self.level == 'trace':
            print(*args)

    def setDebugLevel(self, level):
        self.level = level.lower()


class QQBot:
    def __init__(self):
        self.addr = 'http://127.0.0.1:4321/'
        self.session = None

    def verifySession(self, auth_key):
        """每个Session只能绑定一个Bot，但一个Bot可有多个Session。
        session Key在未进行校验的情况下，一定时间后将会被自动释放"""
        data = {"verifyKey": auth_key}
        url = self.addr+'verify'
        res = requests.post(url, data=json.dumps(data)).json()
        logger.DebugLog(res)
        if res['code'] == 0:
            return res['session']
        return None

    def bindSession(self, session, qq):
        """校验并激活Session，同时将Session与一个已登录的Bot绑定"""
        data = {"sessionKey": session, "qq": qq}
        url = self.addr + 'bind'
        res = requests.post(url, data=json.dumps(data)).json()
        logger.DebugLog(res)
        if res['code'] == 0:
            self.session = session
            return True
        return False

    def releaseSession(self, session, qq):
        """不使用的Session应当被释放，长时间（30分钟）未使用的Session将自动释放，
        否则Session持续保存Bot收到的消息，将会导致内存泄露(开启websocket后将不会自动释放)"""
        data = {"sessionKey": session, "qq": qq}
        url = self.addr + 'release'
        res = requests.post(url, data=json.dumps(data)).json()
        logger.DebugLog(res)
        if res['code'] == 0:
            return True
        return False

    def getMsgFromGroup(self, session):
        url = self.addr + 'fetchLatestMessage?count=10&sessionKey='+session
        res = requests.get(url).json()
        if res['code'] == 0:
            return res['data']
        return None

    def getMessageCount(self, session):
        url = self.addr + 'countMessage?sessionKey='+session
        res = requests.get(url).json()
        if res['code'] == 0:
            return res['data']
        return 0
    
    def sendMsgToGroup(self, session, group, messages):
        sendMessage = []
        for message in messages:
            type = message.msgType
            text = message.msg
            # content1 = "消息：{}".format(text)
            logger.DebugLog(">> 消息类型：" + type)

            print('type:',type,'typeTrans[type]',typeTrans[type],"text",text,'---------------')
            if type in typeTrans:
                sendMessage.append({"type": type, typeTrans[type]: text})
            else:
                logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
                return
            # if type == 'Plain':
            #     sendMessage = [{"type": type, "text": content1}]
            # elif type == 'Image':
            #     sendMessage = [
            #         {"type": 'Plain', "text": content2},
            #         {"type": type, "url": text}]
            # elif type == 'Face':
            #     sendMessage = [{"type": 'Plain', "text": content2},
            #                {"type": type, "faceId": text}]
            # else:
            #     logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
            #     return 0
        data = {
            "sessionKey": session,
            "group": group,
            "messageChain": sendMessage
        }
        logger.DebugLog(">> 消息内容：" + str(data))
        url = self.addr + 'sendGroupMessage'
        try:
            res = requests.post(url, data=json.dumps(data)).json()
        except:
            logger.DebugLog(">> 转发失败")
            return 0
        logger.DebugLog(">> 请求返回：" + str(res))
        if res['code'] == 0:
            return res['messageId']
        return 0

    def sendMsgToAllGroups(self, session, receive_groups, send_groups, msg_data):
        # 对每条消息进行检查
        for msg in msg_data:
            group_id = msg['groupId']
            # 接收的消息群正确（目前只支持 消息类型）
            if group_id in receive_groups:
                # 依次将消息转发到目标群
                for g in send_groups:
                    logger.DebugLog(">> 当前群："+g)
                    if g == group_id:
                        logger.DebugLog(">> 跳过此群")
                        continue
                    res = self.sendMsgToGroup(session, g, msg)
                    if res != 0:
                        logger.TraceLog(">> 转发成功！{}".format(g))

    def sendFriendMessage(self, session, qq, messages):
        sendMessage = []
        for message in messages:
            type = message.msgType
            text = message.msg
            if type in typeTrans:
                sendMessage.append({"type": type, typeTrans[type]: text})
            else:
                logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
                return

        data = {
          "sessionKey": session,
          "target": qq,
          "messageChain": sendMessage
          #   [{ "type": "Plain", "text": msg }, ]
        }
        url = self.addr + 'sendFriendMessage'
        try:
            res = requests.post(url, data=json.dumps(data)).json()
        except:
            logger.DebugLog(">> 发送失败")
            return 0
        if res['code'] == 0:
            return res['messageId']
        return 0

    def parseMsgChain(self, msgChain):
        for message in msgChain:
            if message['type'] == 'Source':
                msgChainList = [MessageRecv(msgType = 'Source', msg = 'None')]
            elif message['type'] == 'Plain':
                msgChainList.append(MessageRecv(msgType = 'Plain', msg = message['text']))
            elif message['type'] == 'At':
                msgChainList.append(MessageRecv(msgType = 'At', msg = message['target']))
            elif message['type'] == 'Image':
                msgChainList.append(MessageRecv(msgType = 'Image', msg = message['url']))
            elif message['type'] == 'Face':
                msgChainList.append(MessageRecv(msgType = 'Face', msg = message['faceId']))
            else:
                logger.TraceLog(">> 当前消息类型暂不支持转发：=> " + message['type'])
                continue
        return msgChainList


    def parseData(self, data):
        res = []
        if data is None:
            return res

        for item in data:
            if item['type'] == 'GroupMessage':
                msgChain = item['messageChain']
                sender = item['sender']
                recv = GroupMessageRecvList(groupId = str(sender['group']['id']), groupName = sender['group']['name'], senderId = str(sender['id']), senderName = sender['memberName'], messageChain = bot.parseMsgChain(msgChain))
                return recv
            elif item['type'] == 'FriendMessage':
                msgChain = item['messageChain']
                sender = item['sender']
                recv = FriendMessageRecvList(senderId = sender['id'], senderName = sender['nickname'],senderRemark = sender['remark'],messageChain = bot.parseMsgChain(msgChain))
                return recv
            else:
                logger.TraceLog(">> 不知道你这从哪来的消息啊：=> " + item['type'])

    def genSendFriendMessage(self, recvData):
        msg = recvData.messageChain
        for m in msg:
            if m.msgType == 'Source':
                sendData = []
            elif m.msgType == 'Plain':
                if m.msg == '/alive':
                    sendData.append(MessageRecv(msgType = 'Plain', msg = '女仆酱生存中'))
            else:
                continue
        return sendData

    def genSendGroupMessage(self, recvData):
        msg = recvData.messageChain
        for m in msg:
            if m.msgType == 'Source':
                sendData = []
            elif m.msgType == 'Plain':
                if m.msg == '/alive':
                    sendData.append(MessageRecv(msgType = 'Plain', msg = '女仆酱生存中'))
            elif m.msgType == 'At':
                if str(m.msg) == '458693766':
                    sendData.append(MessageRecv(msgType = 'Plain', msg = '杜杜？世界上最蠢的人'))
            else:
                continue
        return sendData

    def msgManagement(self, session, send_group, data):

        # 对得到的消息data进行解析
        recvData = bot.parseData(data)
        logger.DebugLog('\n\n解析后的数据 {}'.format(recvData))
        if recvData.groupType == 'GroupMessage':
            sendData = bot.genSendGroupMessage(recvData)
            bot.sendMsgToGroup(session, send_group, sendData)
        elif recvData.groupType == 'FriendMessage':
            sendData = bot.genSendFriendMessage(recvData)
            bot.sendFriendMessage(session, recvData.senderId, sendData)
        #if len(data) == 0:
        #    return

        #if data[0]['type'] == 'Plain':
        #    if data[0]['text'] == '/repeat':
        #        bot.sendMsgToGroup(session, send_group, data[0])
        #    if data[0]['text'] == '你希望有返回的话':
        #        data[0]['text'] = '你希望答复的话'
        #        bot.sendMsgToGroup(session, send_group, data[0])
        #elif data[0]['type'] == 'At':
        #    if data[0]['text'] == '458693766':
        #        data[0]['type'] = 'Plain'
        #        data[0]['text'] = '杜杜大傻逼'
        #        bot.sendMsgToGroup(session, send_group, data[0])


logger = Logger()
bot = QQBot()
app = Flask(__name__)

def qqTransfer():
    with open('conf.json', 'r+', encoding="utf-8") as f:
        content = f.read()
    conf = json.loads(content)

    auth_key = conf['auth_key']
    bind_qq = conf['bind_qq']
    sleep_time = conf['sleep_time']
    debug_level = conf['debug_level']

    receive_groups = conf['receive_groups']
    send_groups = conf['send_groups']

    logger.setDebugLevel(debug_level)

    session = bot.verifySession(auth_key)
    logger.DebugLog(">> session: "+session)
    bot.bindSession(session, bind_qq)
    while True:
        cnt = bot.getMessageCount(session)
        if cnt:
            logger.DebugLog('>> 有消息了 => {}'.format(cnt))
            logger.DebugLog('获取消息内容')
            data = bot.getMsgFromGroup(session)
            if len(data) == 0:
                logger.DebugLog('消息为空')
                continue
            # logger.DebugLog('解析消息内容')
            logger.DebugLog(data)
            bot.msgManagement(session, send_groups[0], data)
            # logger.DebugLog('转发消息内容')
            # bot.sendFriendMessage(session, data[0]['sender']['id'], 'hello')
            # bot.sendMsgToAllGroups(session, receive_groups, send_groups, data)
        # else:
        #     logger.DebugLog('空闲')
        sleep(sleep_time)
    bot.releaseSession(session, bind_qq)


@app.route('/QQ/send', methods=['GET'])
def qqListenMsg():
    # 类似于Qmsg的功能
    # flask做得接收HTTP请求转为QQ消息
    qq = request.args.get('target', None)
    msg = request.args.get('msg', None)
    bot.sendFriendMessage(bot.session, qq, msg)
    return 'Hello World!'

if __name__ == '__main__':
    t = threading.Thread(target=qqTransfer)
    t.setDaemon(True)
    t.start()

    app.run(port='8765', host='0.0.0.0')
