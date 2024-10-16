from nonebot import get_plugin_config, on_message, CommandGroup, get_driver, get_bot
from nonebot.plugin import PluginMetadata
import yaml, openai, json
from .config import Config
from himibot.plugins.keep_safe import is_banned
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from datetime import datetime
import asyncio, random, requests
__plugin_meta__ = PluginMetadata(
    name="chat",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
driver = get_driver()
with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    openai_key = config_dict['openai_key']
    openai_endpoint = config_dict['openai_endpoint']
    deepseek_key = config_dict['deepseek_key'] if 'deepseek_key' in config_dict else None
    deepseek_endpoint = config_dict['deepseek_endpoint'] if 'deepseek_endpoint' in config_dict else None
    bot_self_id = config_dict['bot_self_id'] if 'bot_self_id' in config_dict else None
    bot_http_endpoint = config_dict['bot_http_endpoint'] if 'bot_http_endpoint' in config_dict else None
    bot_http_token = config_dict['bot_http_token'] if 'bot_http_token' in config_dict else None



openai_client = openai.OpenAI(api_key=openai_key, base_url=openai_endpoint)
deepseek_client = openai.OpenAI(api_key=deepseek_key, base_url=deepseek_endpoint)
doodlegpt_enabled = True
platform = 'OpenAI'
openai_model = 'gpt-4o-mini'
max_replies = 5
base_penalty_time = 0.5
max_penalty_time = 8
chat_indicator_base = '>{platform} - {remaining_style}'
remaining_style = ['◆','◇'] # '{remaining * "◆"}{max_replies - remaining * "◇"}'
use_reflection = True
system_prompt_dir = ''
system_prompt_text = ''
start_history = []

def chat_indicator(remaining:int, platform:str):
    return '\n' + chat_indicator_base.format(platform=platform, remaining_style=remaining_style[0] * remaining + remaining_style[1] * (max_replies - remaining))


def safe_int_conversion(value, default):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
    
def safe_float_conversion(value, default):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def continue_chat(user_prompt:str, stream:bool = False, platform:str = 'openai', history:list = start_history.copy()):
    history.append({"role": "user", "content": user_prompt})
    if platform.lower() == "openai":
        return openai_client.chat.completions.create(
            model=openai_model,
            messages=history,
            temperature=0.7,
            stream=stream)
    elif platform.lower() == 'deepseek':
        return deepseek_client.chat.completions.create(
            model='deepseek-chat',
            messages=history,
            stream=stream)

def reset_chat():
    global chat_sessions, reply_ids, start_chat_ids, system_prompt_text, start_history, system_prompt_dir
    system_prompt_dir = 'himibot/doodlegpt-reflection.txt' if use_reflection else 'himibot/doodlegpt.txt'
    with open(system_prompt_dir, 'r', encoding='utf-8') as f:
        system_prompt_text = f.read()
    start_history = [{"role": "system", "content": system_prompt_text}]
    chat_sessions = {'example_chat_id': {'remaining': 0, 'history': start_history.copy(), 'last_bot_message_id': '0', 'reply_style': False}}
    reply_ids = []
    start_chat_ids = []
    sent_sessions = []
    for sessions in chat_sessions:
        if not sessions.startswith('start_'):
            if sessions.startswith('group'):
                group_id = sessions.split('_')[1]
                requests.post(f'{bot_http_endpoint}/send_group_msg', headers={'Authorization': f'Bearer {bot_http_token}'}, json={'group_id': group_id, 'message': [{'type': 'text', 'data': {'text': 'bot即将重载，检测到有未结束的对话。对话记录将被清空。'}}]}) if sessions not in sent_sessions else None
                sent_sessions.append(sessions)
            elif not sessions.startswith('example_'):
                user_id = int(sessions.split('_')[0])
                requests.post(f'{bot_http_endpoint}/send_private_msg', headers={'Authorization': f'Bearer {bot_http_token}'}, json={'user_id': user_id, 'message': [{'type': 'text', 'data': {'text': 'bot即将重载，检测到有未结束的对话。对话记录将被清空。'}}]}) if sessions not in sent_sessions else None

reset_chat()

chat = CommandGroup('dg')
chat_default = chat.command(tuple())
chat_with_reply = chat.command('reply', aliases={'dg r','dgr'})
reply_chat = on_message(rule=to_me(), priority=10)
chat_config = chat.command('config', permission=SUPERUSER)
switch_dg = chat.command('toggle', permission=SUPERUSER, aliases={'dg t','dgt'})
status = chat.command('status', permission=SUPERUSER, aliases={'dg s','dgs'})
clear = chat.command('clear', permission=SUPERUSER, aliases={'dg c','dgc'})
help = chat.command('help', aliases={'dg h','dg ?', 'dgh', 'dg?'})


@chat_default.handle()
async def handle(bot: Bot, event: MessageEvent):
    if event.get_session_id().startswith('group'):
        group_id = event.get_session_id().split('_')[1]
        if is_banned(group_id):
            return
    if doodlegpt_enabled is False:
        await chat_default.finish('对话功能已被禁用。')
    chat_id = 'start_' + event.get_session_id() + '_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    history = start_history.copy()
    message_id = str((await chat_default.send('回复该消息以开始与DoodleGPT对话（样式：无回复）。该消息可重复使用，直到bot重载。\n（提示：回复带有以下指示的消息以继续对话）' + chat_indicator(max_replies, platform)))['message_id'])
    chat_sessions[chat_id] = {'remaining': max_replies, 'history': history, 'last_bot_message_id': message_id, 'reply_style': False}
    start_chat_ids.append(message_id)
    print(start_chat_ids)
    await chat_default.finish()

@chat_with_reply.handle()
async def handle(bot: Bot, event: MessageEvent):
    if event.get_session_id().startswith('group'):
        group_id = event.get_session_id().split('_')[1]
        if is_banned(group_id):
            return
    if doodlegpt_enabled is False:
        await chat_default.finish('对话功能已被禁用。')
    chat_id = 'start_' + event.get_session_id() + '_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    history = start_history.copy()
    user_message_id = event.message_id
    message_id = str((await chat_with_reply.send(Message([MessageSegment.reply(user_message_id), '回复该消息以开始与DoodleGPT对话（样式：有回复）。该消息可重复使用，直到bot重载。\n（提示：回复带有以下指示的消息以继续对话）' + chat_indicator(max_replies, platform)])))['message_id'])
    chat_sessions[chat_id] = {'remaining': 5, 'history': history, 'last_bot_message_id': message_id, 'reply_style': True}
    start_chat_ids.append(message_id)
    print(start_chat_ids)
    await chat_with_reply.finish()

@reply_chat.handle()
async def handle(bot: Bot, event: MessageEvent):
    if event.reply:
        if event.message_type == 'group':
            if is_banned(event.group_id):
                return
            if doodlegpt_enabled is False:
                return
        reply_id=str(event.reply.message_id)
        user_message_id = event.message_id
        if reply_id in (reply_ids + start_chat_ids):
            if reply_id in reply_ids:
                reply_ids.remove(reply_id)
            chat_id = [i for i in chat_sessions if chat_sessions[i]['last_bot_message_id'] == reply_id][0]
            additional_text = ''
            if chat_id.startswith('start_'):
                new_chat_id = event.get_session_id() + '_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                chat_sessions[new_chat_id] = chat_sessions[chat_id].copy()
                chat_sessions[new_chat_id]['last_bot_message_id'] = 0
                chat_id = new_chat_id
                chat_sessions[new_chat_id]['history'][0]['content'] += '\nTime now in UTC+8: ' + datetime.now().strftime('%Y-%m-%d %a %H:%M:%S')
            print(chat_id)
            history = chat_sessions[chat_id]['history']
            remaining = chat_sessions[chat_id]['remaining']
            reply_style = chat_sessions[chat_id]['reply_style']
            if remaining <= 0:
                await reply_chat.finish('对话次数已用完。')
            user_prompt = event.get_plaintext() + additional_text
            if remaining == 1:
                user_prompt += '\n\n(This is our last message. Please say goodbye to me at the end.)'
            response = continue_chat(user_prompt, stream=True, platform=platform, history=history)
            collected_reponse = ''
            message_cache = ''
            response_penalty_time = base_penalty_time
            response_reached_answer = False
            response_use_reflection = False
            try:
                for chunk in response:
                    if chunk.choices[0].finish_reason is None:
                        message_cache += chunk.choices[0].delta.content
                        if '\n' in message_cache:
                            collected_reponse += message_cache
                            message_cache = message_cache.replace('\n', '').strip()
                            if '<analyse>' in message_cache:
                                response_use_reflection = True
                            if message_cache != '' and (response_reached_answer or (response_use_reflection is False)):
                                message = Message([MessageSegment.reply(user_message_id), message_cache]) if reply_style else Message(message_cache)
                                await asyncio.sleep(random.uniform(0.1,0.2) + response_penalty_time)
                                await reply_chat.send(message)
                                response_penalty_time = response_penalty_time * 2 if response_penalty_time < max_penalty_time / 2 else max_penalty_time
                            if '<answer>' in message_cache:
                                response_reached_answer = True
                            message_cache = ''
                    else:
                        remaining -= 1
                        collected_reponse += message_cache
                        message_cache += chat_indicator(remaining, platform) if remaining > 0 else ''
                        message = Message([MessageSegment.reply(user_message_id), message_cache]) if reply_style else Message(message_cache)
                        message_id = (await reply_chat.send(message))['message_id']
                    await asyncio.sleep(random.uniform(0.1,0.2))
                if message_id is not None:
                    history.append({'role': 'assistant', 'content': collected_reponse})
                    print(history)
                    if remaining > 0:
                        chat_sessions[chat_id] = {'remaining': remaining, 'history': history, 'last_bot_message_id': str(message_id), 'reply_style': reply_style}
                        reply_ids.append(str(message_id))
                    else:
                        chat_sessions.pop(chat_id)
                    print(reply_ids)
                else:
                    await reply_chat.finish('对话被中断。请重新开始。')
            except openai.BadRequestError as e:
                await reply_chat.finish('对话被人工智能服务商中断。请重新开始。')

@chat_config.handle()
async def handle(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    global platform, openai_model, max_replies, base_penalty_time, chat_indicator_base, remaining_style, max_penalty_time, use_reflection
    args = arg.extract_plain_text().split()
    if len(args) == 0:
        # Show current configuration
        await chat_config.finish('当前配置：\n' + f'对话平台：{platform}\n对话模型：{openai_model}\n对话次数：{max_replies}\n回车惩罚时间：{base_penalty_time}\n最大回车惩罚时间：{max_penalty_time}\n对话指示：{chat_indicator_base}\n剩余次数样式：{remaining_style}\n使用反射：{use_reflection}')
    elif args[0] in ['platform', 'p']:
        platform = 'openai' if platform == 'deepseek' else 'deepseek'
        await chat_config.finish(f'对话平台已设置为{platform}。')
    elif args[0] in ['model', 'm']:
        openai_model = args[1]
        await chat_config.finish(f'对话模型已设置为{openai_model}。')
    elif args[0] in ['max_replies', 'mr']:
        max_replies = safe_int_conversion(args[1], 5)
        await chat_config.finish(f'对话次数已设置为{max_replies}。')
    elif args[0] in ['base_penalty_time', 'bpt']:
        base_penalty_time = safe_float_conversion(args[1], 0.5)
        await chat_config.finish(f'回车惩罚时间已设置为{base_penalty_time}。')
    elif args[0] in ['max_penalty_time', 'mpt']:
        max_penalty_time = safe_float_conversion(args[1], 10)
        await chat_config.finish(f'最大回车惩罚时间已设置为{max_penalty_time}。')
    elif args[0] in ['chat_indicator_base', 'cib']:
        chat_indicator_base = args[1]
        await chat_config.finish(f'对话指示已设置为{chat_indicator_base}。')
    elif args[0] in ['remaining_style', 'rs']:
        remaining_style = list(args[1])
        await chat_config.finish(f'剩余次数样式已设置为{remaining_style}。')
    elif args[0] in ['use_reflection', 'ur']:
        use_reflection = not use_reflection
        reset_chat()
        await chat_config.finish('目前已' + ('启用' if use_reflection else '禁用') + '反射。')
    else:
        await chat_config.finish('用法：\n'
                                 ':dg config platform(p)：切换对话平台。\n'
                                 ':dg config model(m) <model>：设置对话模型。\n'
                                 ':dg config max_replies(mr) <number>：设置对话次数。\n'
                                 ':dg config base_penalty_time(bpt) <number>：设置回车惩罚时间。\n'
                                 ':dg config max_penalty_time(mpt) <number>：设置最大回车惩罚时间。\n'
                                 ':dg config chat_indicator_base(cib) <text>：设置对话指示。\n'
                                 ':dg config remaining_style(rs) <text>：设置剩余次数样式。\n'
                                 ':dg config use_reflection(ur)：切换是否使用反射。')


@switch_dg.handle()
async def handle(bot: Bot, event: MessageEvent):
    global doodlegpt_enabled
    doodlegpt_enabled = not doodlegpt_enabled
    await switch_dg.finish(f'对话功能已{"启用" if doodlegpt_enabled else "禁用"}。')

@status.handle()
async def handle(bot: Bot, event: MessageEvent):
    active_sessions_ids = [i for i in chat_sessions if not (i.startswith('start_') or i.startswith('example_chat_id'))]
    print(chat_sessions)
    await status.finish(f'对话功能：{"启用" if doodlegpt_enabled else "禁用"}\n对话平台：{platform}\n对话模型：{openai_model}\n活跃的对话列表：{'\n'.join(active_sessions_ids)}')

@clear.handle()
async def handle(bot: Bot, event: MessageEvent):
    reset_chat()
    await clear.finish('已清空所有对话。')


@help.handle()
async def handle(bot: Bot, event: MessageEvent):
    await help.finish('使用方法：\n'
                      ':dg：启动无回复样式的对话。\n'
                      ':dg reply(r)：启动有回复样式的对话。\n')

@driver.on_bot_disconnect
async def disconnect_notice(bot: Bot):
    sent_sessions = []
    for sessions in chat_sessions:
        if not sessions.startswith('start_'):
            if sessions.startswith('group'):
                group_id = sessions.split('_')[1]
                requests.post(f'{bot_http_endpoint}/send_group_msg', headers={'Authorization': f'Bearer {bot_http_token}'}, json={'group_id': group_id, 'message': [{'type': 'text', 'data': {'text': 'bot即将重启，检测到有未结束的对话。对话记录将被清空。'}}]}) if sessions not in sent_sessions else None
                sent_sessions.append(sessions)
            elif not sessions.startswith('example_'):
                user_id = int(sessions.split('_')[0])
                requests.post(f'{bot_http_endpoint}/send_private_msg', headers={'Authorization': f'Bearer {bot_http_token}'}, json={'user_id': user_id, 'message': [{'type': 'text', 'data': {'text': 'bot即将重启，检测到有未结束的对话。对话记录将被清空。'}}]}) if sessions not in sent_sessions else None