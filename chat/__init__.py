from nonebot import get_plugin_config, on_message, CommandGroup, get_driver, get_bot
from nonebot.plugin import PluginMetadata
import yaml, json
from .config import Config
from himibot.plugins.keep_safe import is_banned, text_moderation
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from datetime import datetime
import asyncio, random, requests
import openai
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

openai_client = openai.AsyncOpenAI(api_key=openai_key, base_url=openai_endpoint)
deepseek_client = openai.AsyncOpenAI(api_key=deepseek_key, base_url=deepseek_endpoint)
doodlegpt_enabled = True
platform = 'DeepSeek'
openai_model = 'deepseek/deepseek-v3/community'
deepseek_model = 'deepseek-chat'
max_replies = 5
base_penalty_time = 0.5
max_penalty_time = 8
chat_indicator_base = '>{platform} - {remaining_style}'
remaining_style = ['◆','◇'] # '{remaining * "◆"}{max_replies - remaining * "◇"}'
use_reflection = True
system_prompt_dir = ''
system_prompt_text = ''
start_history = []
max_streams = 10
engage_percentage = 0.1
bot_nickname = 'CodePig2047'
streaming_groups = {'example_group_id': {'remaining': 0, 'history': start_history.copy(), 'last_bot_message_id': '0', 'reply_style': False}}

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

async def continue_chat(user_prompt:str = None, stream:bool = False, platform:str = 'openai', history:list = start_history.copy()):
    history.append({"role": "user", "content": user_prompt}) if user_prompt is not None else None
    if platform.lower().startswith("openai"):
        return await openai_client.chat.completions.create(
            model=openai_model,
            messages=history,
            stream=stream)
    elif platform.lower().startswith('deepseek'):
        return await deepseek_client.chat.completions.create(
            model=deepseek_model,
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

async def get_history(group_id: int, fetch_message_count: int, bot: Bot, ignore_self = True):
    fetch_message_count = fetch_message_count if fetch_message_count > 0 else 21
    messages_from_api = await bot.get_group_msg_history(group_id=group_id, count=fetch_message_count)
    messages='Chat messages fetched at UTC+8' + datetime.now().strftime("%Y-%m-%d %a %H:%M:%S") + ':\n'
    valid_message_counter = 0
    messages_from_api['messages'].pop()
    for message in messages_from_api['messages']:
        if message['user_id'] == bot_self_id and ignore_self:
            continue
        sender_nickname = message['sender']['nickname']
        # Extract text content if present
        message_content = ""
        for part in message['message']:
            if part['type'] == 'text':
                message_text = str(part['data']['text'])
                message_content += message_text if not (message_text.startswith(':') or message_text.startswith('/')) else ''
        
        # Only print messages that have text content
        if message_content:
            messages += f"{sender_nickname}: {message_content}\n"
            valid_message_counter += 1
    return messages, valid_message_counter

reset_chat()

async def in_streaming_group(event: GroupMessageEvent) -> bool:
    return str(event.group_id) in streaming_groups and not event.get_plaintext().startswith(':')

async def in_chat(event: MessageEvent) -> bool:
    return (str(event.reply.message_id) in (reply_ids + start_chat_ids) and doodlegpt_enabled) if event.reply else False
    
chat = CommandGroup('dg')
chat_default = chat.command(tuple())
chat_with_reply = chat.command('reply', aliases={'dg r','dgr'})
reply_chat = on_message(rule=to_me() & in_chat, priority=5)
chat_config = chat.command('config', permission=SUPERUSER)
switch_dg = chat.command('toggle', permission=SUPERUSER, aliases={'dg t','dgt'})
status = chat.command('status', permission=SUPERUSER, aliases={'dg s','dgs'})
clear = chat.command('clear', permission=SUPERUSER, aliases={'dg c','dgc'})
help = chat.command('help', aliases={'dg h','dg ?', 'dgh', 'dg?'})
join = chat.command('join')
leave = chat.command('leave')
chat_streaming = on_message(rule=in_streaming_group)


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
        response = await continue_chat(user_prompt, stream=True, platform=platform, history=history)
        collected_reponse = ''
        message_cache = ''
        response_penalty_time = base_penalty_time
        response_reached_answer = False
        response_use_reflection = False
        try:
            async for chunk in response:
                if chunk.choices[0].finish_reason is None:
                    message_cache += chunk.choices[0].delta.content or ''
                    if '\n' in message_cache:
                        collected_reponse += message_cache
                        message_cache = message_cache.replace('\n', '').strip()
                        if '<think>' in message_cache:
                            response_use_reflection = True
                        if message_cache != '' and (response_reached_answer or (response_use_reflection is False)):
                            moderation_result = text_moderation(message_cache, message_id=chat_id)
                            if moderation_result['Suggestion'] != 'Block':
                                message = Message([MessageSegment.reply(user_message_id), message_cache]) if reply_style else Message(message_cache)
                                await asyncio.sleep(random.uniform(0.1,0.2) + response_penalty_time)
                                await reply_chat.send(message)
                                response_penalty_time = response_penalty_time * 2 if response_penalty_time < max_penalty_time / 2 else max_penalty_time
                            else:
                                await reply_chat.finish(f'对话中包含不当内容。请重新开始（类型：{moderation_result["Label"]}，来源：{moderation_result["Source"]}）。')
                        if '</think>' in message_cache:
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
    global platform, openai_model, max_replies, base_penalty_time, chat_indicator_base, remaining_style, max_penalty_time, use_reflection, max_streams, engage_percentage
    args = arg.extract_plain_text().split()
    if len(args) == 0:
        # Show current configuration
        await chat_config.finish('当前配置：\n' + f'对话平台：{platform}\n对话模型：{openai_model}\n对话次数：{max_replies}\n回车惩罚时间：{base_penalty_time}\n最大回车惩罚时间：{max_penalty_time}\n对话指示：{chat_indicator_base}\n剩余次数样式：{remaining_style}\n使用反射：{use_reflection}\n最大参与对话数：{max_streams}\n参与对话概率：{engage_percentage}')
    elif args[0] in ['platform', 'p']:
        if len(args) < 2:
            platform = 'openai' if platform == 'deepseek' else 'deepseek'
        else:
            platform = args[1]
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
    elif args[0] in ['max_streams', 'ms']:
        max_streams = safe_int_conversion(args[1], 10)
        await chat_config.finish(f'最大参与对话数已设置为{max_streams}。')
    elif args[0] in ['engage_percentage', 'ep']:
        engage_percentage = safe_float_conversion(args[1], 0.1)
        await chat_config.finish(f'参与对话概率已设置为{engage_percentage}。')
    else:
        await chat_config.finish('用法：\n'
                                 ':dg config platform(p)：切换对话平台。\n'
                                 ':dg config model(m) <model>：设置对话模型。\n'
                                 ':dg config max_replies(mr) <number>：设置对话次数。\n'
                                 ':dg config base_penalty_time(bpt) <number>：设置回车惩罚时间。\n'
                                 ':dg config max_penalty_time(mpt) <number>：设置最大回车惩罚时间。\n'
                                 ':dg config chat_indicator_base(cib) <text>：设置对话指示。\n'
                                 ':dg config remaining_style(rs) <text>：设置剩余次数样式。\n'
                                 ':dg config use_reflection(ur)：切换是否使用反射。\n'
                                    ':dg config max_streams(ms) <number>：设置最大参与对话数。\n'
                                    ':dg config engage_percentage(ep) <number>：设置参与对话概率。')


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

@join.handle()
async def handle(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    global streaming_groups
    if is_banned(str(event.group_id)):
        return
    if str(event.group_id) in streaming_groups:
        await join.finish('DoodleGPT 已在本群聊天。')
    arg = args.extract_plain_text()
    group_name = (await bot.get_group_info(group_id=event.group_id))['group_name']
    initial_prompt, count = '', 0
    if safe_int_conversion(arg, 0) > 0:
        past_messages, count = await get_history(event.group_id, safe_int_conversion(arg, 20), bot, ignore_self=False)
        past_messages.replace(bot_nickname, 'DoodleGPT')
        initial_prompt = f"Below are some messages before you joined the group:\n{past_messages}\n(You can cue some of them.)"
    streaming_groups[str(event.group_id)] = {'remaining': max_streams, 'history': [{"role": "system", "content": system_prompt_text + f'你现在在群"{group_name}"里聊天。每次只回应一个话题，保持消息在三行以内！用换行分割每句话，没有值得回复的话题时主动抛梗聊天。记住：唠嗑要像真人那样分多次参与讨论，严禁合并回复多个用户/话题！'}, {"role": "user", "content": f"{initial_prompt}\nNow greet your group members."}], 'reply_style': False}
    await join.send(f'DoodleGPT 已查看之前的{count}条文字消息并加入到本群。')
    response = await continue_chat(stream=True, platform=platform, history=streaming_groups[str(event.group_id)]['history'])
    collected_reponse = ''
    message_cache = ''
    response_penalty_time = base_penalty_time
    response_reached_answer = False
    response_use_reflection = False
    try:
        async for chunk in response:
            if chunk.choices[0].finish_reason is None:
                message_cache += chunk.choices[0].delta.content or ''
                if '\n' in message_cache:
                    collected_reponse += message_cache
                    message_cache = message_cache.replace('\n', '').strip()
                    if '<think>' in message_cache:
                        response_use_reflection = True
                    if message_cache != '' and (response_reached_answer or (response_use_reflection is False)):
                        moderation_result = text_moderation(message_cache, message_id=f'{event.group_id}_{event.message_id}')
                        if moderation_result['Suggestion'] != 'Block':
                            message = Message(message_cache)
                            await asyncio.sleep(random.uniform(0.1,0.2) + response_penalty_time)
                            await bot.send_group_msg(group_id=event.group_id, message=message)
                            response_penalty_time = response_penalty_time * 2 if response_penalty_time < max_penalty_time / 2 else max_penalty_time
                        else:
                            await join.finish(f'对话中包含不当内容。请重新开始（类型：{moderation_result["Label"]}，来源：{moderation_result["Source"]}）。')
                    if '</think>' in message_cache:
                        response_reached_answer = True
                    message_cache = ''
            else:
                collected_reponse += message_cache
                message = Message(message_cache)
                await asyncio.sleep(random.uniform(0.1,0.2))
                await bot.send_group_msg(group_id=event.group_id, message=message)
            streaming_groups[str(event.group_id)]['history'].append({'role': 'assistant', 'content': collected_reponse})
            streaming_groups[str(event.group_id)]['history'].append({'role': 'user', 'content': ''})
    except openai.BadRequestError as e:
        return
    except openai.APIError as e:
        return


@leave.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    global streaming_groups
    if is_banned(str(event.group_id)):
        return
    if str(event.group_id) not in streaming_groups:
        await leave.finish('DoodleGPT 没在本群聊天。')
    streaming_groups.pop(str(event.group_id))
    await leave.finish('DoodleGPT 已离开本群。')

@chat_streaming.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    if is_banned(str(event.group_id)):
        return
    if doodlegpt_enabled is False:
        return
    remaining, history, reply_style = streaming_groups[str(event.group_id)]['remaining'], streaming_groups[str(event.group_id)]['history'], streaming_groups[str(event.group_id)]['reply_style']
    history[-1]['content'] += f'\n{event.sender.nickname}: {event.get_plaintext()}' if remaining > 0 else f'\n{event.sender.nickname}: {event.get_plaintext()}\n(You are now sending your last message before you leave the group chat. Say goodbye to members engaged in the chat at the end of your message.)'
    if (random.random() >= engage_percentage) and remaining != 0 and not event.is_tome():
        return
    else:
        response = await continue_chat(stream=True, platform=platform, history=history)
        collected_reponse = ''
        message_cache = ''
        response_penalty_time = base_penalty_time
        response_reached_answer = False
        response_use_reflection = False
        try:
            async for chunk in response:
                if chunk.choices[0].finish_reason is None:
                    message_cache += chunk.choices[0].delta.content or ''
                    if '\n' in message_cache:
                        collected_reponse += message_cache
                        message_cache = message_cache.replace('\n', '').strip()
                        if '<think>' in message_cache:
                            response_use_reflection = True
                        if message_cache != '' and (response_reached_answer or (response_use_reflection is False)):
                            message = Message([MessageSegment.reply(event.message_id), message_cache]) if reply_style else Message(message_cache)
                            await asyncio.sleep(random.uniform(0.1,0.2) + response_penalty_time)
                            await bot.send_group_msg(group_id=event.group_id, message=message)
                            response_penalty_time = response_penalty_time * 2 if response_penalty_time < max_penalty_time / 2 else max_penalty_time
                        if '</think>' in message_cache:
                            response_reached_answer = True
                        message_cache = ''
                else:
                    collected_reponse += message_cache
                    message = Message([MessageSegment.reply(event.message_id), message_cache]) if reply_style else Message(message_cache)
                    await asyncio.sleep(random.uniform(0.1,0.2))
                    await bot.send_group_msg(group_id=event.group_id, message=message)
            if remaining > 0:
                history.append({'role': 'assistant', 'content': collected_reponse})
                history.append({'role': 'user', 'content': ''})
                print(remaining)
                remaining -= 1
                streaming_groups[str(event.group_id)] = {'remaining': remaining, 'history': history, 'reply_style': reply_style}
            else:
                streaming_groups.pop(str(event.group_id))
        except openai.BadRequestError as e:
            return
        except openai.APIError as e:
            return