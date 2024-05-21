from nonebot import get_plugin_config, on_command, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from .config import Config
import yaml
__plugin_meta__ = PluginMetadata(
    name="locale",
    description="",
    usage="",
    config=Config,
)
user_locale_cache = {}

from himibot.plugins.userdata import get_user_data, update_user_data
config = get_plugin_config(Config)

known_locales = ['zh-cn', 'zh-tw', 'en-us', 'en-gb', 'zh-yue']
class Locale:
    punctuations_english = [', ', '. ', '? ', '! ', ': ', '; ', '...', '"', '"', "'", "'"]
    punctuations_chinese = ['，', '。', '？', '！', '：', '；', '……', '“', '”', '‘', '’']
    languages = {
        'zh-cn': {'locale_friendly_name': '简体中文', 'punctuations': punctuations_chinese, 'language': {'your_current_locale_is': '您当前的语言是：{language}。', 'available_locales': '可用语言：', 'locale_not_found': '找不到这个语言。', 'locale_set_success': '语言设置成功。目前语言为{language}。', 'hello': '你好！欢迎用{language}和我交流！'}},
        'zh-tw': {'locale_friendly_name': '繁體中文', 'fallback': 'zh-cn', 'punctuations': punctuations_chinese, 'language': {'your_current_locale_is': '您當前的語系是：', 'available_locales': '可用語系：', 'locale_not_found': '找不到這個語系。', 'locale_set_success': '語系設定成功。當前語系為{language}。', 'hello': '你好！歡迎用{language}和我聊天！'}},
        'en-us': {'locale_friendly_name': 'English (United States)', 'fallback': 'en-gb', 'punctuations': punctuations_english, 'language': {'your_current_locale_is': 'Your current locale is: ', 'available_locales': 'Available locales: ', 'locale_not_found': 'Locale not found!', 'locale_set_success': 'Locale set successfully! Current locale is {language}.', 'hello': 'Hello! Welcome to chat with me in {language}!'}},
        'en-gb': {'locale_friendly_name': 'English (United Kingdom)', 'fallback': 'en-us', 'punctuations': punctuations_english, 'language': {}},
        'zh-yue': {'locale_friendly_name': '粤語', 'fallback': 'zh-tw', 'punctuations': punctuations_chinese, 'language': {'your_current_locale_is': '你當前嘅語言係：', 'available_locales': '可用語言：', 'locale_not_found': '搵不到呢個語言。', 'locale_set_success': '語言設定成功。依家嘅語言係{language}。', 'hello': '你好！歡迎用{language}同我傾偈！'}}
    }
def get_locale_text(locale: str, key: str = None, module: str = None):
    if module is None:
        localeclass = Locale
    else:
        localeclass = getattr(Locale, module)
    if locale not in known_locales:
        locale = 'zh-cn'
    if key is None:
        return localeclass.languages[locale]['locale_friendly_name']
    if fallback := localeclass.languages[locale].get('fallback', ''):
        return localeclass.languages[locale]['language'].get(key, localeclass.languages[fallback]['language'].get(key, ''))
    return localeclass.languages[locale]['language'].get(key, '')


locale_cmd = CommandGroup('locale')
locale = locale_cmd.command(tuple())
locale_set = locale_cmd.command('set')
locale_list = locale_cmd.command('list')
locale_hello = locale_cmd.command('hello')

@locale.handle()
async def handle_locale(bot, event: Event):
    user_id = event.get_user_id()
    user_data = get_user_data(user_id)
    await locale.finish(get_locale_text(user_data[2], 'your_current_locale_is') + get_locale_text(user_data[2]))

@locale_set.handle()
async def handle_locale_set(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    set_locale = args.extract_plain_text()
    if set_locale in known_locales:
        update_user_data(user_id, 'locale', set_locale)
        await locale_set.finish(get_locale_text(set_locale, 'locale_set_success').format(language=get_locale_text(set_locale)))
    else:
        await locale_set.finish(get_locale_text(set_locale, 'locale_not_found'))

@locale_list.handle()
async def handle_locale_list(event: Event):
    user_locale = get_user_data(event.get_user_id())[2]
    list_display = get_locale_text(user_locale, 'available_locales')
    for i in known_locales:
        list_display += '\n' + i + ', ' + get_locale_text(i)
    await locale_list.finish(list_display)

@locale_hello.handle()
async def handle_locale_hello(event: Event):
    user_locale = get_user_data(event.get_user_id())[2]
    await locale_hello.finish(get_locale_text(user_locale, 'hello').format(language=get_locale_text(user_locale)))