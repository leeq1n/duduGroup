from dataclasses import dataclass
# 'Source': 'id+time',
typeTrans = {'Plain': 'text', 'At': 'target', 'Image': 'url', 'Face': 'faceId', 'File': 'id+name+size'}

@dataclass
class MessageRecv:
    msgType: str
    msg: str
    
@dataclass
class GroupMessageRecvList:
    groupId: str
    groupName: str
    senderId: str
    senderName: str
    messageChain: list
    groupType: str = 'GroupMessage'
    # messageChain: list[GroupMessageRecv]

@dataclass
class FriendMessageRecvList:
    senderId: str
    senderName: str
    senderRemark: str
    messageChain: list
    groupType: str = 'FriendMessage'

# @dataclass
# class GroupMessageSendList:
#     groupId: str
#     groupName: str
#     msgType: str
#     msg: str

# @dataclass
# class DOSendGroupAt:
