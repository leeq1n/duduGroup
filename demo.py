import json
import os

import requests
from flask import Flask, request
from time import sleep
import threading

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

    def parseGroupMsg(self, data):
        res = []
        if data is None:
            return res
        for item in data:
            if item['type'] == 'GroupMessage':
                type = item['messageChain'][-1]['type']
                if type == 'Image':
                    text = item['messageChain'][-1]['url']
                elif type == 'Plain':
                    text = item['messageChain'][-1]['text']
                elif type == 'Face':
                    text = item['messageChain'][-1]['faceId']
                elif type == 'At':
                    text = str(item['messageChain'][-1]['target'])
                else:
                    logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
                    continue
                name = item['sender']['memberName']
                group_id = str(item['sender']['group']['id'])
                group_name = item['sender']['group']['name']
                res.append({'text': text, 'type': type, 'name': name, 'groupId': group_id, 'groupName': group_name})
        return res

    def getMessageCount(self, session):
        url = self.addr + 'countMessage?sessionKey='+session
        res = requests.get(url).json()
        if res['code'] == 0:
            return res['data']
        return 0

def sendPokeMsgToGroup(self, session, group, msg):
        text = msg['text']
        type = msg['type']
        name = msg['name']
        group_id = msg['groupId']
        group_name = msg['groupName']
        content1 = "消息：{}".format(text)
        # content1 = "【消息中转助手】\n用户：{}\n群号：{}\n群名：{}\n消息：\n{}".format(
        #     name, group_id, group_name, text)
        # content2 = "【消息中转助手】\n用户：{}\n群号：{}\n群名：{}\n消息：\n".format(
        #     name, group_id, group_name)
        logger.DebugLog(">> 消息类型：" + type)
        if type == 'Plain':
            message = [{"type": type, "text": content1}]
        elif type == 'Image':
            message = [
                {"type": 'Plain', "text": content2},
                {"type": type, "url": text}]
        elif type == 'Face':
            message = [{"type": 'Plain', "text": content2},
                       {"type": type, "faceId": text}]
        else:
            logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
            return 0
        data = {
                "sessionKey": session,
                "group": group,
                "messageChain": message
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

    def sendMsgToGroup(self, session, group, msg):
        text = msg['text']
        type = msg['type']
        name = msg['name']
        group_id = msg['groupId']
        group_name = msg['groupName']
        content1 = "消息：{}".format(text)
        # content1 = "【消息中转助手】\n用户：{}\n群号：{}\n群名：{}\n消息：\n{}".format(
        #     name, group_id, group_name, text)
        # content2 = "【消息中转助手】\n用户：{}\n群号：{}\n群名：{}\n消息：\n".format(
        #     name, group_id, group_name)
        logger.DebugLog(">> 消息类型：" + type)
        if type == 'Plain':
            message = [{"type": type, "text": content1}]
        elif type == 'Image':
            message = [
                {"type": 'Plain', "text": content2},
                {"type": type, "url": text}]
        elif type == 'Face':
            message = [{"type": 'Plain', "text": content2},
                       {"type": type, "faceId": text}]
        else:
            logger.TraceLog(">> 当前消息类型暂不支持转发：=> "+type)
            return 0
        data = {
                "sessionKey": session,
                "group": group,
                "messageChain": message
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

    def sendFriendMessage(self, session, qq, msg):
        data = {
          "sessionKey": session,
          "target": qq,
          "messageChain": [
            { "type": "Plain", "text": msg },
          ]
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

    def msgManagement(self, session, send_group, data):
        # 传参：
        # session为对话窗口，send_group为需要发送消息的群号，data[0]为第一条消息
        # 说明：
        # data[0]['text']为群里刚收到的文本
        # 如果需要更改发送的消息，请按照如下格式:
        # data[0]['text'] = '消息'
        data = bot.parseGroupMsg(data)
        logger.DebugLog(data)
        if len(data) == 0:
            return

        if data[0]['type'] == 'Plain':
            if data[0]['text'] == '/repeat':
                bot.sendMsgToGroup(session, send_group, data[0])
            if data[0]['text'] == '你希望有返回的话':
                data[0]['text'] = '你希望答复的话'
                bot.sendMsgToGroup(session, send_group, data[0])
        elif data[0]['type'] == 'At':
            if data[0]['text'] == '458693766':
                data[0]['type'] = 'Plain'
                data[0]['text'] = '杜杜大傻逼'
                bot.sendMsgToGroup(session, send_group, data[0])


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
