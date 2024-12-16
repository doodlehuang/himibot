from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_request
from nonebot.adapters.onebot.v11 import Bot, RequestEvent
import time

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="group_request_handle",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

async def group_join_request_rule(event: RequestEvent) -> bool:
    return event.request_type == 'group' and event.sub_type == 'add'

group_join_request = on_request(priority=5, rule=group_join_request_rule, block=True)

@group_join_request.handle()
async def handle_group_join_request(bot: Bot, event: RequestEvent):
    answer = event.comment.split('答案：')[1].strip() if '答案：' in event.comment else event.comment
    if answer == 'password':
        await event.approve(bot)
        await bot.send_group_msg(group_id=event.group_id, message=f'新成员QQ号：{event.user_id}\n加入时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
    else:
        await event.reject(bot, reason='请提供正确的验证信息。')
    await group_join_request.finish()