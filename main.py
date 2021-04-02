import asyncio


from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
from graia.application.friend import Friend
from graia.application.group import Group, Member

from app.core.config import *
from app.core.controller import Controller
from app.extend.github import github_listener

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=host,  # 填入 httpapi 服务运行的地址
        authKey=authKey,  # 填入 authKey
        account=qq,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)


@bcc.receiver("FriendMessage")
async def friend_message_listener(message: MessageChain, friend: Friend, app: GraiaMiraiApplication):
    event = Controller(message, friend, app)
    await event.process_event()


@bcc.receiver("GroupMessage")
async def group_message_listener(message: MessageChain, group: Group, member: Member, app: GraiaMiraiApplication):
    event = Controller(message, group, member, app)
    await event.process_event()


loop.create_task(github_listener(app))
app.launch_blocking()
