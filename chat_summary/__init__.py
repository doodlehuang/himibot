from nonebot import get_plugin_config, on_command, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from himibot.plugins.chat import get_history
from .config import Config
import datetime, openai, yaml
from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name="chat_summary",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    openai_key = config_dict['openai_key']
    openai_endpoint = config_dict['openai_endpoint']
    deepseek_key = config_dict['deepseek_key'] if 'deepseek_key' in config_dict else None
    deepseek_endpoint = config_dict['deepseek_endpoint'] if 'deepseek_endpoint' in config_dict else None
    bot_self_id = config_dict['bot_self_id'] if 'bot_self_id' in config_dict else 0
    go_to_groups = config_dict['go_to_groups'] if 'go_to_groups' in config_dict else {}

print(go_to_groups)
openai_client = openai.OpenAI(api_key=openai_key, base_url=openai_endpoint)
deepseek_client = openai.OpenAI(api_key=deepseek_key, base_url=deepseek_endpoint)
start_history = [{"role": "system", "content": 'You are an AI assistant tasked with summarizing chat conversations in Chinese. Your job is to provide a concise and coherent summary of the entire conversation in one natural paragraph. The summary should focus on the main topics discussed in the chat without listing messages verbatim. Avoid using any markdown formatting, symbols, or line breaks. Aim to convey the essence of the exchange in a clear and topic-oriented manner.'}]
openai_model = 'gpt-4o-mini'
user_cooldown_list = {'example_user_id': 10}

summary = CommandGroup('summary')
get_history_message = summary.command(tuple(), aliases={'summarize', '总结', 'sum'})
cooldown_list = summary.command('cd', permission=SUPERUSER)
cooldown_clear = summary.command('cdc', permission=SUPERUSER)
supersummary = summary.command('super', permission=SUPERUSER, aliases={'sumper'})
help = summary.command('help', aliases={'帮助', 'help'})
cooldown_minutes = 3

def safe_int_conversion(value, default=20):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

@get_history_message.handle()
async def handle(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    group_id = event.group_id
    user_id = str(event.user_id)
    if user_id in user_cooldown_list:
        remaining_time = user_cooldown_list[user_id]
        await get_history_message.finish(f'您还需等待{remaining_time}分钟才能再次使用此功能。')
    fetch_message_count = safe_int_conversion(args.extract_plain_text()) + 1
    messages, valid_message_counter = await get_history(group_id, fetch_message_count, bot)
    history = start_history.copy()
    history.append({"role": "user", "content": messages})
    try: 
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=history,
            temperature=0.7,
            stream=False)
        summary = response.choices[0].message.content
        successful_model = 'gpt-4o-mini'
    except openai.BadRequestError as e:
        try:
            await get_history_message.send('OpenAI 请求失败，尝试使用 DeepSeek 模型...')
            response = deepseek_client.chat.completions.create(
                model='deepseek-chat',
                messages=history,
                stream=False)
            summary = response.choices[0].message.content
            successful_model = 'deepseek-chat'
        except openai.BadRequestError as e:
            summary = str(e)
            successful_model = 'none'
    user_cooldown_list[user_id] = cooldown_minutes
    await get_history_message.finish(f'成功使用 {successful_model} 模型总结了本群 {valid_message_counter} 条文字消息，总结如下：\n{summary}\n请等待{cooldown_minutes}分钟后再次使用此功能。') if successful_model != 'none' else await get_history_message.finish(f'无法使用任何模型总结文字消息。')    

@scheduler.scheduled_job("interval", minutes=1, id="purge_cooldown")
async def purge_cooldown():
    global user_cooldown_list
    user_to_be_removed = []
    for user_id, remaining_time in user_cooldown_list.items():
        remaining_time -= 1
        if remaining_time <= 0:
            user_to_be_removed += [user_id]
        else:
            user_cooldown_list[user_id] = remaining_time
    user_cooldown_list = {k: v for k, v in user_cooldown_list.items() if k not in user_to_be_removed}


@cooldown_list.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    await cooldown_list.finish(user_cooldown_list)

@cooldown_clear.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    user_cooldown_list.clear()
    await cooldown_clear.finish('已清除所有用户的冷却时间。')

@help.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    await help.finish('使用方法：\n'
                      '输入 :sum [数字] 来获取最近的消息记录并总结。\n'
                      '管理员命令：\n'
                      ':summary cd - 查看用户冷却时间。\n'
                      ':summary cdc - 清除所有用户的冷却时间。')
    
@supersummary.handle()
async def handle(bot: Bot, event: MessageEvent, args = CommandArg()):
    args = args.extract_plain_text().split(' ')
    if len(args) < 1:
        await supersummary.finish('请输入正确的参数。')
    elif len(args) < 2:
        args.append('100')
    group_id = args[0]
    if group_id in go_to_groups:
        group_id = go_to_groups[group_id]
    group_name = (await bot.get_group_info(group_id=group_id))['group_name']
    arg = int(args[1])
    fetch_message_count = safe_int_conversion(args[1], 100) + 1
    messages, valid_message_counter = await get_history(group_id, fetch_message_count, bot)
    history = start_history.copy()
    history.append({"role": "user", "content": messages})
    try: 
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=history,
            temperature=0.7,
            stream=False)
        summary = response.choices[0].message.content
        successful_model = 'gpt-4o-mini'
    except openai.BadRequestError as e:
        try:
            await supersummary.send('OpenAI model failed, trying Deepseek model...')
            response = deepseek_client.chat.completions.create(
                model='deepseek-chat',
                messages=history,
                stream=False)
            summary = response.choices[0].message.content
            successful_model = 'deepseek-chat'
        except openai.BadRequestError as e:
            summary = str(e)
            successful_model = 'none'
    if successful_model == 'none':
        await supersummary.finish(f'无法使用任何模型总结来自 {group_name} 的文字消息。')
    await supersummary.finish(f'成功使用 {successful_model} 模型总结了来自 {group_name} 的 {valid_message_counter} 条文字消息，总结如下：\n{summary}')