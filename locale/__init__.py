from nonebot import get_plugin_config, on_command, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from .config import Config
import yaml
import os
from pathlib import Path

__plugin_meta__ = PluginMetadata(
    name="locale",
    description="",
    usage="",
    config=Config,
)

user_locale_cache = {}
locale_data_cache = {}

from himibot.plugins.userdata import get_user_data, update_user_data
config = get_plugin_config(Config)

known_locales = ['zh-cn', 'zh-tw', 'en-us', 'en-gb', 'zh-yue']

def load_locale_file(locale: str):
    if locale in locale_data_cache:
        return locale_data_cache[locale]
    
    try:
        l10n_path = Path(__file__).parent.parent.parent / 'l10n'
        with open(l10n_path / f'{locale}.yml', 'r', encoding='utf-8') as f:
            locale_data = yaml.safe_load(f)
            locale_data_cache[locale] = locale_data
            return locale_data
    except Exception as e:
        print(f"Error loading locale file {locale}: {e}")
        return None

def get_locale_text(locale: str, plugin: str, key: str, fallback_locale: str = 'zh-cn', visited_locales: set = None):
    """
    获取本地化文本
    :param locale: 语言代码
    :param plugin: 插件名称
    :param key: 文本键，支持使用点号分隔的路径（如 'broadcast.help'）
    :param fallback_locale: 回退语言
    :param visited_locales: 已访问过的语言集合（用于防止循环依赖）
    :return: 本地化文本
    """
    if visited_locales is None:
        visited_locales = set()
    
    if locale in visited_locales:
        return f"{plugin}.{key}"
    visited_locales.add(locale)
    
    locale_data = load_locale_file(locale)
    if not locale_data:
        if locale != fallback_locale:
            return get_locale_text(fallback_locale, plugin, key, fallback_locale, visited_locales)
        return f"{plugin}.{key}"
    
    try:
        if plugin == 'locale' and key == 'locale_friendly_name':
            return locale_data.get(plugin, {}).get('locale_friendly_name', f"{plugin}.{key}")
        
        # 处理带点号的键路径
        current = locale_data.get(plugin, {})
        if '.' in key:
            for part in key.split('.'):
                if isinstance(current, dict):
                    current = current.get(part, None)
                    if current is None:
                        break
                else:
                    current = None
                    break
            text = current
        else:
            text = current.get(key, None)

        if text is None:
            # 如果当前语言找不到文本，尝试使用该语言的 fallback
            current_fallback = locale_data.get('locale', {}).get('fallback')
            if current_fallback and current_fallback not in visited_locales:
                return get_locale_text(current_fallback, plugin, key, fallback_locale, visited_locales)
            # 如果没有设置 fallback 或 fallback 已访问过，使用默认的 fallback
            elif locale != fallback_locale:
                return get_locale_text(fallback_locale, plugin, key, fallback_locale, visited_locales)
        return text if text is not None else f"{plugin}.{key}"
    except Exception as e:
        print(f"Error getting locale text: {e}")
        return f"{plugin}.{key}"

locale_cmd = CommandGroup('locale')
locale = locale_cmd.command(tuple())
locale_set = locale_cmd.command('set')
locale_list = locale_cmd.command('list')
locale_hello = locale_cmd.command('hello')
locale_reload = locale_cmd.command('reload', permission=SUPERUSER)

@locale.handle()
async def handle_locale(bot, event: Event):
    user_id = event.get_user_id()
    user_data = get_user_data(user_id)
    current_locale = user_data[2]
    await locale.finish(
        get_locale_text(current_locale, 'locale', 'your_current_locale_is').format(
            language=get_locale_text(current_locale, 'locale', 'locale_friendly_name')
        )
    )

@locale_set.handle()
async def handle_locale_set(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    set_locale = args.extract_plain_text()
    current_locale = get_user_data(user_id)[2]
    
    if set_locale in known_locales:
        update_user_data(user_id, 'locale', set_locale)
        await locale_set.finish(
            get_locale_text(set_locale, 'locale', 'locale_set_success').format(
                language=get_locale_text(set_locale, 'locale', 'locale_friendly_name')
            )
        )
    else:
        await locale_set.finish(get_locale_text(current_locale, 'locale', 'locale_not_found'))

@locale_list.handle()
async def handle_locale_list(event: Event):
    user_locale = get_user_data(event.get_user_id())[2]
    list_display = get_locale_text(user_locale, 'locale', 'available_locales')
    for i in known_locales:
        list_display += '\n' + i + ', ' + get_locale_text(i, 'locale', 'locale_friendly_name')
    await locale_list.finish(list_display)

@locale_hello.handle()
async def handle_locale_hello(event: Event):
    user_locale = get_user_data(event.get_user_id())[2]
    await locale_hello.finish(
        get_locale_text(user_locale, 'locale', 'hello').format(
            language=get_locale_text(user_locale, 'locale', 'locale_friendly_name')
        )
    )

@locale_reload.handle()
async def handle_locale_reload(event: Event):
    locale_data_cache.clear()
    await locale_reload.finish(get_locale_text(get_user_data(event.get_user_id())[2], 'locale', 'locale_reload_success'))