from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command, require, on_startswith
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText
from nonebot.rule import is_type
from .config import Config
from nonebot.permission import SUPERUSER
from nonebot.adapters.telegram.event import MessageEvent as TEvent


__plugin_meta__ = PluginMetadata(
    name="callme",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
from himibot.plugins.userdata import get_user_data, update_user_data

# callme = on_command('callme', priority=5)
callmewipe = on_command('callme-wipe', priority=5)
callme_telegram = on_startswith('/callme', rule=is_type(TEvent), priority=5)
callmewipe_telegram = on_startswith('/callmewipe', rule=is_type(TEvent), priority=3, block=True)

# @callme.handle()
# async def handle(matcher: Matcher, bot, event: Event, args: Message = CommandArg()):
#     user_id = event.get_user_id()
#     nickname = get_user_data(user_id)[1]
#     if text := args.extract_plain_text():
#         matcher.set_arg("nickname", text)
#         nickname = text
#     if nickname:
#         await callme.finish(f"你好{nickname}({user_id})！")

# @callme.got("nickname", prompt="你想让我叫你什么呢？")
# async def got_nickname(bot, event: Event, nickname: str = ArgPlainText()):
#     if nickname == "":
#         await callme.reject("请换个名字吧，你还想让我叫你什么呢？")
#     user_id = event.get_user_id()
#     update_user_data(user_id, "nickname", nickname)
#     await callme.finish(f"你好{nickname}({user_id})！")

# @callme.handle()
# async def handle(bot, event: Event):
#     await callme.finish("该功能正在维护中，暂时无法使用。你仍可使用callme-wipe来清除你的称呼。")
    
@callme_telegram.handle()
async def handle(event: TEvent):
    user_id = event.get_user_id()
    nickname = get_user_data(user_id)[1]
    if text:= event.get_message().extract_plain_text()[8:]:
        user_id = event.get_user_id()
        update_user_data(user_id, "nickname", text)
        await callme_telegram.finish(f"你好{text}({user_id})！")
    elif nickname:
        await callme_telegram.finish(f"你好{nickname}({user_id})！")
    else:
        await callme_telegram.finish("请在 /callme 后输入你想让我叫你的名字。")

@callmewipe.handle()
async def handle(bot, event: Event):
    user_id = event.get_user_id()
    update_user_data(user_id, "nickname", "")
    await callmewipe.finish("好的，你可以选用新的称呼了。")

@callmewipe_telegram.handle()
async def handle(event: TEvent):
    user_id = event.get_user_id()
    update_user_data(user_id, "nickname", "")
    await callmewipe_telegram.finish("好的，你可以选用新的称呼了。")