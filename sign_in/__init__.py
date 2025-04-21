from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from datetime import date
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="sign_in",
    description="",
    usage="",
    config=Config,
)
# print(date.today())
config = get_plugin_config(Config)

