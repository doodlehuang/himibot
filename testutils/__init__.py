from nonebot import get_plugin_config, CommandGroup, require
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent as Event, Bot, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import is_type
import yaml, json
from jsonpath import jsonpath
import os
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from himibot.plugins.keep_safety import is_banned
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="testutils",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
whois_list = {}
cooldown_list = []
def load_whois():
    global whois_list
    if 'whois.yaml' not in os.listdir():
        with open('whois.yaml', 'w', encoding='utf-8') as f:
            yaml.dump({}, f, allow_unicode=True)
    with open('whois.yaml', 'r', encoding='utf-8') as f:
        whois_list = yaml.safe_load(f)

def save_whois():
    with open('whois.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(whois_list, f, allow_unicode=True)
@scheduler.scheduled_job("interval", minutes=2, id="remove_cooldown")
async def remove_cooldown():
    global cooldown_list
    cooldown_list = []

load_whois()
whois_commands = CommandGroup('whois')
whois = whois_commands.command(tuple())
whois_list_cmd = whois_commands.command('list')
whois_add = whois_commands.command('add', permission=SUPERUSER)
whois_remove = whois_commands.command('remove', permission=SUPERUSER)
whois_load = whois_commands.command('load', permission=SUPERUSER)
whois_help = whois_commands.command('help')
whois_find = whois_commands.command('find')
whois_cue = whois_commands.command('cue', aliases={'whois q', 'whois.q'}, rule=is_type(GroupMessageEvent))

@whois.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        print(is_banned(event.group_id))
        if is_banned(event.group_id):
            return
    reply = event.original_message['reply']
    isreply = False
    args_text = args.extract_plain_text().strip()
    at_msg = event.original_message['at']
    if at_msg:
        user_id = at_msg[0].data['qq']
    elif args_text:
        if args_text in whois_list:
            user_id = args_text
        else:
            matched_users = list()
            keywords = args_text.split(' ')
            for arg in keywords:
                for user_id in whois_list:
                    for alias in whois_list[user_id]:
                        if arg in alias.lower():
                            matched_users.append(user_id)
                            break
            if matched_users:
                print(matched_users)
                message = ''
                for user_id in matched_users:
                    nickname = (await bot.get_stranger_info(user_id=user_id))['nickname']
                    print(nickname)
                    message += f'{nickname}({user_id})常被称为' + '、'.join(whois_list[user_id]) + '。\n'
                await whois.finish(message.strip())
            else:
                await whois.finish('没找到。')
    else:
        user_id = str(event.get_user_id())
    if reply:
        user_id = str((await bot.get_msg(message_id=reply[0].data['id']))['sender']['user_id'])
        isreply = True
    print(user_id)
    if user_id in whois_list:
        message = Message()
        if isreply:
            message.append(MessageSegment.reply(reply[0].data['id']))
        nickname = (await bot.get_stranger_info(user_id=user_id))['nickname']
        message.append(f'{nickname}({user_id})常被称为' + '、'.join(whois_list[user_id]) + '。')
        await whois.finish(message)
    else:
        await whois.finish('不知道这谁。')

@whois_help.handle()
async def handle(event: Event):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    await whois_help.finish('可用的命令及解释：\nwhois list：列出所有用户的别名。\nwhois find <alias>：查找某个别名对应的用户。\nwhois cue/q <alias>：向某人发出寻找请求。\nwhois add <@/user_id> <alias1> (alias2) (...)：为某用户添加别名（仅限机器人管理）。\nwhois remove <@/user_id> <alias1> (alias2) (...)：为某用户删除别名（仅限机器人管理）。\nwhois load：加载别名列表（仅限机器人管理）。')

@whois_list_cmd.handle()
async def handle(bot: Bot, event: Event):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    message = Message()
    for user_id in whois_list:
        nickname = (await bot.get_stranger_info(user_id=user_id))['nickname']
        message +=  f'{nickname}({user_id})常被称为' + '、'.join(whois_list[user_id]) + '。\n'
    await whois_list_cmd.finish(message)

@whois_add.handle()
async def handle(bot: Bot, event: Event, message: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    global whois_list
    args = message.extract_plain_text().strip()
    reply = event.original_message['reply']
    if args == '':
        await whois_add.finish('用法：whois add <@/user_id> <alias1> (alias2) (...)')
    args = args.split()
    at_msg = event.original_message['at']
    if at_msg:
        user_id = at_msg[0].data['qq']
        index = 0
    elif reply:
        user_id = str((await bot.get_msg(message_id=reply[0].data['id']))['sender']['user_id'])
        index = 0
    else:
        user_id = args[0]
        index = 1
    aliases = args[index:]
    if user_id not in whois_list:
        whois_list[user_id] = []
    for alias in aliases:
        if alias not in whois_list[user_id]:
            whois_list[user_id].append(alias)
    save_whois()
    await whois_add.finish('添加成功。所以这个人叫' + '、'.join(whois_list[user_id]) + '。')

@whois_remove.handle()
async def handle(bot: Bot, event: Event, message: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    global whois_list
    args = message.extract_plain_text().strip()
    reply = event.original_message['reply']
    if not args:
        await whois_remove.finish('用法：whois remove <user_id> <alias1> (alias2) (...)')
    args = args.split()
    at_msg = event.original_message['at']
    if at_msg:
        user_id = at_msg[0].data['qq']
        index = 0
    elif reply:
        user_id = str((await bot.get_msg(message_id=reply[0].data['id']))['sender']['user_id'])
        index = 0
    else:
        user_id = args[0]
        index = 1
    if user_id not in whois_list:
        await whois_remove.finish('不知道这谁。')
    aliases = args[index:]
    for alias in aliases:
        if alias in whois_list[user_id]:
            whois_list[user_id].remove(alias)
    save_whois()
    if whois_list[user_id]:
        await whois_remove.finish('删除成功。现在这个人叫' + '、'.join(whois_list[user_id]) + '。')
    else:
        await whois_remove.finish('删除成功。这个人没名了。')

@whois_load.handle()
async def handle(event: Event):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    load_whois()
    await whois_load.finish('加载成功，共记载了' + str(len(whois_list)) + '个用户的别名。')

@whois_find.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    args = str(args).strip().lower()
    if args == '':
        await whois_find.finish('用法：whois find <alias>')
    args = args.split(' ')
    matched_users = list()
    for arg in args:
        for user_id in whois_list:
            for alias in whois_list[user_id]:
                if arg in alias.lower():
                    matched_users.append(user_id)
                    break
    if matched_users:
        message = ''
        for user_id in matched_users:
            nickname = (await bot.get_stranger_info(user_id=user_id))['nickname']
            print(nickname)
            message += f'{nickname}({user_id})常被称为' + '、'.join(whois_list[user_id]) + '。\n'
        await whois_find.finish(message.strip())
    else:
        await whois_find.finish('没找到。')

@whois_cue.handle()
async def handle(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if is_banned(event.group_id):
        return
    global cooldown_list
    sender_id = str(event.sender.user_id)
    args_text = args.extract_plain_text().strip()
    if args_text == '':
        await whois_cue.finish('用法：whois cue/q <alias>\n一次只能cue一个人，因此请准确地输入其称呼（大小写敏感）。\n该功能有约1-2分钟的冷却时间（且众生平等）。')
    if sender_id in cooldown_list:
        await whois_cue.finish('你的操作太频繁了，请稍后再试。（冷却时间为1-2分钟。）')
    group_id = str(event.group_id)
    member_list_json = json.dumps(await bot.get_group_member_list(group_id=group_id))
    member_list = jsonpath(json.loads(member_list_json), '$..user_id')
    name = args_text.split(' ')[0]
    matched_users = [user_id for user_id in whois_list if name in whois_list[user_id]]
    if matched_users:
        if matched_users[0] == sender_id:
            await whois_cue.finish('你找你自己是吧。')
        if int(matched_users[0]) not in member_list:
            await whois_cue.finish('换个群再试吧。')
        print(matched_users)
        message = Message()
        message.append(MessageSegment.at(matched_users[0]))
        message.append('，')
        message.append(MessageSegment.at(event.get_user_id()))
        message.append(' 想找你。')
        cooldown_list.append(sender_id)
        await whois_cue.finish(message)
    else:
        await whois_cue.finish('没找到。')