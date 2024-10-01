from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters import Event
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Message as OMessage, MessageEvent as OEvent

import yaml
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="ping",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    superuser_id = config_dict['superuser_id'] if 'superuser_id' in config_dict else '0'
ping = on_command("ping", priority=5, permission=SUPERUSER, block=True)
# atme = on_message(priority=10, block=True, rule=to_me())
say = on_command("say", priority=5, permission=SUPERUSER, block=True)
send = on_command("send", priority=5, permission=SUPERUSER, block=True)
say_normal = on_command("say", priority=7, block=True)
@ping.handle()
async def handle(bot, event: Event, args: Message = CommandArg()):
    session_id = event.get_session_id()
    user_id = event.get_user_id()
    if session_id.startswith("group"):
        group_id = session_id.split("_")[1]
        group_prompt = "(" + group_id + ")"
    if text := args.extract_plain_text():
        await ping.finish(text + " pong " + "to " + user_id + group_prompt + "!")
    else:
        await ping.finish("pong " + "to " + user_id + group_prompt + "!")
@say.handle()
async def handle(args: Message = CommandArg()):
    if text := args.extract_plain_text():
        await say.finish(text)
    else:
        await say.finish("say what?")

@say_normal.handle()
async def handle():
    await say_normal.finish("who are you?")
@send.handle()
async def handle(bot: Bot, event: OEvent, args: Message = CommandArg()):
    if str(event.user_id) != superuser_id:
        print('1')
        return
    if text := args.extract_plain_text():
        target = text.split(' ')[0]
        if len(text.split(' ')) > 1:
            msg = text.split(' ', 1)[1]
            await bot.send_msg(message=OMessage(msg), group_id=target)
            return
    else:
        await send.finish("send what?")