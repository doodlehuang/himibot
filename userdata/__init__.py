from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from .config import Config
import sqlite3
__plugin_meta__ = PluginMetadata(
    name="userdata",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
registered_users = {}
def database_user_init():
    database = sqlite3.connect('userdata.db')
    cursor = database.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS userdata
        (userid TEXT PRIMARY KEY NOT NULL,
        nickname TEXT,
        locale TEXT,
        pronoun TEXT,
        monerium TEXT,
        permission_level INTEGER,
        last_sign_in_date TEXT,
        additional_data TEXT)''')
    database.commit()
    cursor.close()
    database.close()
def database_group_init():
    database = sqlite3.connect('groupdata.db')
    cursor = database.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS groupdata
        (groupid TEXT PRIMARY KEY NOT NULL,
        name TEXT,
        locale TEXT,
        permission_level INTEGER,
        additional_data TEXT)''')
    database.commit()
    cursor.close()
    database.close()

database_user_init()
user_database = sqlite3.connect('userdata.db')
user_cursor = user_database.cursor()

def auto_user_data(user_id: str):
    cursor = user_database.cursor()
    if user_id in registered_users:
        return
    cursor.execute('SELECT * FROM userdata WHERE userid = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO userdata (userid, nickname, locale, pronoun, monerium, permission_level, last_sign_in_date, additional_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, 'None', 'zh-cn', 'None', '0', '0', 'None', 'None'))
        user_database.commit()
        registered_users[user_id] = True
    user_cursor.close()

def get_user_data(user_id: str):
    cursor = user_database.cursor()
    cursor.execute('SELECT * FROM userdata WHERE userid = ?', (user_id,))
    result = cursor.fetchone()
    if result is None:
        auto_user_data(user_id)
        cursor.execute('SELECT * FROM userdata WHERE userid = ?', (user_id,))
        result = cursor.fetchone()
    cursor.close()
    return result

def get_user_data_soft(user_id: str):
    user_cursor.execute('SELECT * FROM userdata WHERE userid = ?', (user_id,))
    result = user_cursor.fetchone()
    if result is None:
        result = ('error')
    return result

def update_user_data(user_id: str, key: str, value: str):
    cursor = user_database.cursor()
    cursor.execute('SELECT * FROM userdata WHERE userid = ?', (user_id,))
    assertion = cursor.fetchone()
    if assertion is None:
        auto_user_data(user_id)
    cursor.execute('UPDATE userdata SET ' + key + ' = ? WHERE userid = ?', (value, user_id)) if key in ['nickname', 'locale', 'pronoun', 'monerium', 'permission_level', 'last_sign_in_date', 'additional_data'] else None
    user_database.commit()
    cursor.close()