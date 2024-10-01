from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command, on_request
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, RequestEvent
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from himibot.plugins.keep_safe import is_banned
import time
import asyncio

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="ping",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

# 存储等待添加的好友请求
friend_requests = {}
group_requests = {}

friend = on_command('friend', priority=5)
addgroup = on_command('addgroup', priority=5, permission=SUPERUSER)
friend_request = on_request(priority=5, block=True)

# 在群成员使用 friend 时，在一分钟内接受好友请求
@friend.handle()
async def handle_friend(bot: Bot, event: GroupMessageEvent):
    user_id = event.user_id
    group_id = event.group_id
    if is_banned(group_id):
        return
    if user_id in friend_requests:
        await friend.send('请不要频繁发送好友请求！')
    else:
        friend_requests[user_id] = time.time()
        await friend.send('请在一分钟内发送好友请求！')
        await asyncio.sleep(60)
        if user_id in friend_requests:
            del friend_requests[user_id]

@addgroup.handle()
async def handle_addgroup(bot: Bot, event: Event, args: Message = CommandArg()):
    group_id = args.extract_plain_text()
    if group_id == '':
        await addgroup.finish('请提供群号！')
    else:
        group_requests[group_id] = time.time()
        await addgroup.send('请在一分钟内邀请我进群！')
        await asyncio.sleep(60)
        if group_id in group_requests:
            del group_requests[group_id]

@friend_request.handle()
async def handle_friend_request(bot: Bot, event: RequestEvent):
    if event.request_type == 'friend':
        user_id = event.user_id
        if user_id in friend_requests:
            del friend_requests[user_id]
            await bot.set_friend_add_request(flag=event.flag, approve=True)
            await asyncio.sleep(3)
            await bot.send_private_msg(user_id=user_id, message='你好！')
        else:
            await bot.set_friend_add_request(flag=event.flag, approve=False)
    elif event.request_type == 'group' and event.sub_type == 'invite':
        group_id = event.group_id
        if group_id in group_requests:
            del group_requests[group_id]
            await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=True)