from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command, on_startswith
from nonebot.adapters import Event
from nonebot.rule import is_type
from nonebot.adapters.telegram.event import MessageEvent as TEvent
from himibot.plugins.keep_safe import is_banned
from nonebot.adapters.discord import MessageSegment
from nonebot.adapters.discord.commands import on_slash_command
import aiohttp
import yaml
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="ss-ana",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    ss_ana_endpoint = config_dict['ss_ana_endpoint'] if 'ss_ana_endpoint' in config_dict else ''
ss_ana_discord = on_slash_command(name="ss-ana", description='获取一条林槐语录。')
ss_ana_telegram = on_startswith('/ss-ana', rule=is_type(TEvent))
ss_ana = on_command("ss-ana", priority=5, aliases={'lhyl', '林槐语录', 'ss'}, block=True)

async def get_ss_ana():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ss_ana_endpoint) as response:
                r = await response.json()
                return(r['text'] + '\n（' + r['time'].split('/')[0] + '年' + str(int(r['time'].split('/')[1])) + '月）')
    except aiohttp.ClientError as e:
        return('获取失败：' + str(e))
    
@ss_ana_discord.handle()
async def handle():
    await ss_ana_discord.send_deferred_response()
    await ss_ana_discord.finish(MessageSegment.text(get_ss_ana()))

@ss_ana_telegram.handle()
async def handle(event: TEvent):
    await ss_ana_telegram.finish(get_ss_ana())

@ss_ana.handle()
async def handle(event: Event):
    if event.get_session_id().startswith('group'):
        group_id = event.get_session_id().split('_')[1]
        if is_banned(group_id):
            return
    await ss_ana.finish(get_ss_ana())