from nonebot import get_plugin_config, on_type, on_command
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GroupBanNoticeEvent as BanEvent
import asyncio
import yaml
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="keep_safe",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
banned_from = dict()
with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    superuser_id = yaml.safe_load(f)['superuser_id']
def load_banned_from():
    global banned_from
    with open('banned_from.yaml', 'r', encoding='utf-8') as f:
        banned_from = yaml.safe_load(f)

def save_banned_from():
    with open('banned_from.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(banned_from, f, allow_unicode=True)
async def count_down_my_unban(group_id: str | int = None, time: int = 60):
    global banned_from
    await asyncio.sleep(time)
    if str(group_id) in banned_from:
        banned_from.pop(str(group_id))
        save_banned_from()
notice_status = False
ban_me = on_type(BanEvent, rule=to_me())
clear_ban_status = on_command('clear_ban_status', permission=SUPERUSER)
list_ban_status = on_command('list_ban_status', permission=SUPERUSER)
set_ban_notice = on_command('set_ban_notice', permission=SUPERUSER)

@ban_me.handle()
async def handle(bot: Bot, event: BanEvent):
    global banned_from
    if event.sub_type == 'ban':
        banned_from[str(event.group_id)] = event.time, str(event.operator_id)
        save_banned_from()
        print(banned_from)
        send = await bot.send_private_msg(user_id=superuser_id, message=f'我在群{event.group_id}被禁言了。其执行者为{event.operator_id}。') if notice_status else None
        await count_down_my_unban(event.group_id, event.duration)
    elif event.sub_type == 'lift_ban':
        if str(event.group_id) in banned_from:
            banned_from.pop(str(event.group_id))
        save_banned_from()
        print(banned_from)
        send = await bot.send_private_msg(user_id=superuser_id, message=f'群{event.group_id}已将我解除了禁言。其执行者为{event.operator_id}。') if notice_status else None

@clear_ban_status.handle()
async def handle(bot: Bot, event):
    global banned_from
    banned_from = dict()
    save_banned_from()
    await clear_ban_status.finish('已清空禁言状态。')

def is_banned(group_id: str | int = None):
    return str(group_id) in banned_from

@list_ban_status.handle()
async def handle(bot: Bot, event):
    global banned_from
    await list_ban_status.finish(str(banned_from))

@set_ban_notice.handle()
async def handle(bot: Bot, event):
    global notice_status
    notice_status = not notice_status
    await set_ban_notice.finish(f'已将禁言通知状态设为{notice_status}。')