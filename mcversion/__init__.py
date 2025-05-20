from nonebot import get_plugin_config, on_command, get_bot, CommandGroup, require
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from .config import Config
from .mcv import get_latest_version
import yaml, asyncio, aiohttp, json

__plugin_meta__ = PluginMetadata(
    name="mcversion",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    bot_self_id = config_dict['bot_self_id'] if 'bot_self_id' in config_dict else None
    ntfy_endpoint = config_dict['ntfy_endpoint'] if 'ntfy_endpoint' in config_dict else None
    ntfy_push_key = config_dict['ntfy_push_key'] if 'ntfy_push_key' in config_dict else None
    mcversion_groups_list = config_dict['mcversion_groups_list'] if 'mcversion_groups_list' in config_dict else []

async def send_ntfy_message(version, release_time, type):
    if ntfy_endpoint and ntfy_push_key:
        async with aiohttp.ClientSession() as session:
            async with session.post(ntfy_endpoint,
                                  data=json.dumps({
                                      "topic": "mcversion",
                                      "message": f"Minecraft {version} {'快照' if type == 'snapshot' else '正式版'}于 {release_time.strftime('%Y-%m-%d %a %H:%M:%S')} UTC 发布",
                                      "title": f'Minecraft 更新',
                                      "tags": ["pick"],
                                      "click": 'https://www.minecraft.net/articles'
                                  }),
                                  headers={
                                      "Authorization": f"Bearer {ntfy_push_key}"
                                  },
                                  timeout=120) as response:
                await response.text()

async def send_group_message(version, release_time, type, group_id):
    try:
        bot = get_bot(str(bot_self_id))
    except Exception as e:
        bot = None
    if bot: 
        message = f'Minecraft {version} {'快照' if type == "snapshot" else "正式版"}于 {release_time.strftime("%Y-%m-%d %a %H:%M:%S")} UTC 发布'
        tasks = [bot.send_group_msg(group_id=group_id, message=message) for group_id in mcversion_groups_list]
        if tasks:
            await asyncio.gather(*tasks)

old_data = None
@scheduler.scheduled_job("interval", minutes=5, id="check-minecraft-version")
async def check_minecraft_version():
    """
    定时检查Minecraft版本更新
    """
    global old_data
    state, data = await get_latest_version()
    changed_versions = []
    if state:
        old_data = data if old_data is None else old_data
        if data.versions() != old_data.versions():
            for version in data: changed_versions.append(version) if not old_data.contains(version) else None
        old_data = data
    for version in changed_versions:
        await send_ntfy_message(version.version, version.release_time, version.type)

mcv_group = CommandGroup('mcv')

mcv_default = mcv_group.command(tuple())
mcv_tune = mcv_group.command('tune', permission=SUPERUSER)
mcv_help = mcv_group.command('help')

@mcv_default.handle()
async def handle(event: Event):
    state, latest_versions = await get_latest_version()
    if state and latest_versions:
        message = '目前最新的 Minecraft 版本为'
        for version in latest_versions:
            message += f"\n{'快照' if version.type == 'snapshot' else '正式版'}: {version.version} ({version.release_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
        await mcv_default.finish(message)

@mcv_tune.handle()
async def handle(event: GroupMessageEvent):
    global mcversion_groups_list
    if str(event.group_id) in mcversion_groups_list:
        mcversion_groups_list.remove(event.group_id)
        await mcv_tune.send('已取消订阅 Minecraft 版本更新通知')
    else:
        mcversion_groups_list.append(event.group_id)
        await mcv_tune.send('已订阅 Minecraft 版本更新通知')
    with open('himibot/config.yml', 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
        config_dict['mcversion_groups_list'] = mcversion_groups_list
    with open('himibot/config.yml', 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, allow_unicode=True)

@mcv_help.handle()
async def handle(event: Event):
    await mcv_help.finish('使用方法:\n:mcv 获取最新版本\n:mcv tune 订阅/取消订阅 Minecraft 版本更新通知\n:mcv help 获取帮助')