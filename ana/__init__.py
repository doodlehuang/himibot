from nonebot import get_plugin_config, on_command, CommandGroup, on_startswith
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from himibot.plugins.keep_safe import is_banned
from .config import Config
from random import choice, random
import httpx
import os

__plugin_meta__ = PluginMetadata(
    name="ana",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
images = {}
image_cats = []
def update_images():
    global images, image_cats
    images = {}
    image_cats = []
    if os.path.exists('himibot/imgs/'):
        for d in next(os.walk(os.path.abspath('himibot/imgs/')))[1]:
            print(d)
            if d not in ['.cache', 'SyncTrash'] and d not in image_cats and not d.startswith('_'):
                images[d] = []
                image_cats.append(d.lower())
                images[d] = [i.lower() for i in os.listdir('himibot/imgs/' + d) if i.split('.')[-1] in ['png', 'gif', 'jpg']]
        return images, image_cats
    else:
        return None
update_images()
imgtest = on_command("imgtest", priority=5, block=True)
# ak = CommandGroup('ak')
# ak_default = ak.command(tuple(), aliases={':k', '：k'})
# ak_list = ak.command('list')
ana = CommandGroup('ana')
ana_default = ana.command(tuple(), aliases={'quote', ':', '：'})
ana_reload = ana.command('reload', permission=SUPERUSER, aliases={'quote reload', 'quote.reload', ':reload', '：reload'})
ana_add = ana.command('add', permission=SUPERUSER, aliases={'quote add', 'quote.add', ':add', '：add'})
ana_list = ana.command('list', aliases={'quote list', 'quote.list', ':list', '：list'})
ana_help = ana.command('help', aliases={'quote help', 'quote.help', ':help', '：help'})

@scheduler.scheduled_job("interval", minutes=10, id="update_ana")
async def update_ana():
    return update_images()

@imgtest.handle()
async def handle(bot: Bot, event: MessageEvent):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    await imgtest.finish(MessageSegment.image('file:///' + os.path.abspath('test.png')))

# @ak_default.handle()
# async def handle(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
#     if event.message_type == 'group':
#         if is_banned(event.group_id):
#             return
#     if args:
#         s = args.extract_plain_text().lower().split(' ')
#         candidates = [i for i in images['kk'] if s[0] in i]
#         if len(s) > 1:
#             for arg in s[1:]:
#                 candidates = [i for i in candidates if arg in i]
#         if candidates:
#             await ak_default.finish(MessageSegment.image('file:///' + os.path.abspath('himibot/imgs/kk/' + choice(candidates))))
#         else:
#             await ak_default.finish('未找到符合条件的语录图。')
#     else:
#         await ak_default.finish(MessageSegment.image('file:///' + os.path.abspath('himibot/imgs/kk/' + choice(images['kk']))))

# @ak_list.handle()
# async def handle(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
#     if event.message_type == 'group':
#         if is_banned(event.group_id):
#             return
#     if args:
#         s = args.extract_plain_text().lower()
#         candidates = [i for i in images['kk'] if s in i]
#         if candidates:
#             await ak_list.finish('在' + str(len(images['kk'])) + '张中找到' + str(len(candidates)) + '张符合搜索条件的语录图：\n' + '\n'.join(candidates))
#         else:
#             await ak_list.finish('未找到符合条件的语录图。')
#     else:
#         await ak_list.finish('共有' + str(len(images['kk'])) + '张语录图：\n' + ', '.join(images['kk']))


@ana_reload.handle()
async def handle(bot: Bot, event: MessageEvent):
    update_images()
    await ana_reload.finish('已使用管理员权限重载出' + str(sum([len(images[i]) for i in image_cats])) + '张语录图。')

@ana_default.handle()
async def handle(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    arglist = args.extract_plain_text().lower().split(' ')
    if len(arglist) > 0:
        candidates = []
        if len(arglist) > 1:
            if arglist[1] == '_' and arglist[0] in image_cats:
                candidates = images[arglist[0]]
                if len(arglist) > 2:
                    for arg in arglist[2:]:
                        candidates = [i for i in candidates if arg in i]
                if candidates:
                    await ana_default.finish(MessageSegment.image('file:///' + os.path.abspath('himibot/imgs/' + arglist[0] + '/' + choice(candidates))))
                else:
                    await ana_default.finish('未在库' + arglist[0] + '中找到语录图。')
        for d in image_cats:
            candidates += [d + '/' + i for i in images[d] if arglist[0] in i]
        candidates += [arglist[0] + '/' + i for i in images[arglist[0]]] if arglist[0] in image_cats else []
        if len(arglist) > 1:
            for arg in arglist[1:]:
                candidates = [i for i in candidates if arg in i]
        if candidates:
            await ana_default.finish(MessageSegment.image('file:///' + os.path.abspath('himibot/imgs/' + choice(candidates))))
        else:
            await ana_default.finish('未找到相关语录图。')
        

@ana_list.handle()
async def handle(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    if args:
        arglist = args.extract_plain_text().lower().split(' ')
        candidates = []
        if len(arglist) > 0:
            if len(arglist) > 1:
                if arglist[1] == '_' and arglist[0] in image_cats:
                    candidates = images[arglist[0]]
                    if len(arglist) > 2:
                        for arg in arglist[2:]:
                            candidates = [i for i in candidates if arg in i]
                    if candidates:
                        await ana_list.finish('找到' + str(len(candidates)) + '张符合搜索条件的语录图：\n' + '\n'.join(candidates))
                    else:
                        await ana_list.finish('未在库' + arglist[0] + '中找到语录图。')
            for d in image_cats:
                candidates += [d + '/' + i for i in images[d] if arglist[0] in i]
            candidates += [arglist[0] + '/' + i for i in images[arglist[0]]] if arglist[0] in image_cats else []
            if len(arglist) > 1:
                for arg in arglist[1:]:
                    candidates = [i for i in candidates if arg in i]
            if candidates:
                await ana_list.finish('找到' + str(len(candidates)) + '张符合搜索条件的语录图：\n' + '\n'.join(candidates))
            else:
                await ana_list.finish('未找到相关语录图。')
    else:
        await ana_list.finish('共有' + str(sum([len(images[i]) for i in image_cats])) + '张语录图：\n' + '\n'.join([i + ': ' + str(len(images[i])) for i in image_cats]))

@ana_help.handle()
async def handle(bot: Bot, event: MessageEvent):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    await ana_help.finish('使用方法：\n'
                          '不带任何参数时，将随机返回一张语录图。\n'
                          '(list) [关键词/库名] [关键词/"_"] [关键词] ...\n'
                          '关键词为语录图文件名的一部分，可以输入多个关键词，以匹配满足所有关键词的语录图。\n'
                          '为避免混淆，当第二个关键词为“_”时，将只搜索所指定的库中的语录图。\n'
                          '可选的搜索命令为“list”，将列出汇总或符合条件的文件。\n'
                          '目前暂不支持由非管理员重载语录图库，或提交新的语录图。')
    
@ana_add.handle()
async def handle(bot: Bot, event: MessageEvent, arg = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    reply = event.original_message['reply'][0]
    if reply:
        msg = (await bot.get_msg(message_id=reply.data['id']))['message']
        img = [i for i in msg if i['type'] == 'image']
        if img:
            img = img[0]['data']
        else:
            await ana_add.finish('请对着有图片的消息回复。')
        text = [i for i in msg if i['type'] == 'text']
        if text:
            text = text[0]['data']['text']
        imgext = img['file'].split('.')[-1]
        imgurl = img['url']
        args = arg.extract_plain_text().lower().split(' ')
        if len(args) < 2:
            args_others = text.lower().split(' ')
            if len(args) == 1:
                args.append(args[0])
                args[0] = args_others[2]
            else:
                args = args_others[2:]
            if args[1] == '':
                args[1] = args_others[3].replace('\n', '')
        if len(args) > 1:
            if args[0] in image_cats or args[0].startswith('_'):
                if imgext in ['png', 'gif', 'jpg']:
                    req = ''
                    try: 
                        req = httpx.get(imgurl)
                    except Exception as e:
                        await ana_add.finish('添加语录图失败：' + str(e))
                    with open('himibot/imgs/' + args[0] + '/' + args[1] + '.' + imgext, 'wb') as f:
                        f.write(req.content)
                    update_images()
                    await ana_add.finish('已添加语录图“' + args[1] + '”至库' + args[0] + '。')
                    
                else:
                    await ana_add.finish('不支持的文件类型。')
            else:
                await ana_add.finish('未找到指定的库。')
        else:
            await ana_add.finish('参数不足。')
    else:
        await ana_add.finish('请对着有图片的消息回复。')
