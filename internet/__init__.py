from nonebot import get_plugin_config, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.adapters import Bot, Message, Event
from himibot.plugins.keep_safe import is_banned
import requests, datetime
from bs4 import BeautifulSoup
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="internet",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
mihomo_proxy = 'http://127.0.0.1:7897'
proxies= {'http': mihomo_proxy, 'https': mihomo_proxy}
no_proxies =  {'http': '', 'https': ''}
def http_test(url = 'http://cp.cloudflare.com', use_proxy = False):
    try:
        http_response = requests.head(url, proxies = proxies, timeout = 3 if use_proxy else no_proxies)
        return http_response.status_code
    except requests.exceptions.RequestException:
        return False
    
def blocked_without_proxy(url = 'http://cp.cloudflare.com'):
    try:
        requests.head(url, proxies = no_proxies, timeout = 3)
        return False
    except requests.exceptions.RequestException:
        try:
            requests.head(url, proxies = proxies, timeout = 3)
            return True
        except requests.exceptions.RequestException:
            return False
        
def extract_prefdomain_url(proxies = no_proxies):
    content = requests.get('https://www.google.com', proxies=proxies).text
    soup = BeautifulSoup(content, 'html.parser')
    
    # 提取href中包含'setprefdomain'的链接
    link = soup.find('a', href=lambda href: href and 'setprefdomain' in href)
    
    if link:
        href = link['href']
        domain = href.split('//')[1].split('/')[0]
        prefdom = href.split('=')[1].split('&')[0]
        print(domain, prefdom)
        if domain and prefdom:
            if domain == 'www.google.com.hk' and prefdom == 'US':
                return 'CN'
            else:
                return prefdom
    else:
        return '（无法获取）'

def raw_githubusercontent_speed_test():
    try:
        start = datetime.datetime.now()
        requests.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', proxies=no_proxies)
        end = datetime.datetime.now()
        time_without_proxy = end - start
        return time_without_proxy.total_seconds(), 'direct'
    except requests.RequestException:
        try:
            start = datetime.datetime.now()
            requests.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', proxies=proxies)
            end = datetime.datetime.now()
            time_with_proxy = end - start
            return time_with_proxy.total_seconds(), 'proxy'
        except requests.RequestException:
            return False, False
        
internet = CommandGroup('internet')
test = internet.command(tuple(), aliases={'net'})

@test.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    if len(args) == 0:
        output = 'HTTP测试：\n'
        http_result = http_test()
        output += f'成功，状态码为{http_result}\n' if http_result else '失败\n'
        output += 'HTTPS测试：\n'
        https_result = http_test('https://cp.cloudflare.com')
        output += f'成功，状态码为{https_result}\n' if https_result else '失败\n'
        output += 'Google 访问状况：'
        google_result = blocked_without_proxy('https://www.google.com/generate_204')
        if not google_result:
            output += f'直接连接（{extract_prefdomain_url()}）'
        else:
            output += f'连接成功（{extract_prefdomain_url(proxies)}）'
        output += '\n'
        output += 'Raw GitHub User Content 访问测试：\n'
        speed, method = raw_githubusercontent_speed_test()
        if speed:
            output += '直接' if method == 'direct' else ''
            output += f'连接速度为{speed*1000:.2f}ms\n'
        await test.finish(output)
    else:
        url = args.extract_plain_text()
        if not url.startswith('http'):
            url = 'http://' + url
        output = f'URL 测试：\n'
        if blocked_without_proxy(url):
            output += 'BIC: Yes\n'
            http_result = http_test(url, True)
            output += f'成功，状态码为{http_result}' if http_result else '失败'
        else:
            output += 'BIC: No\n'
            http_result = http_test(url)
            output += f'成功，状态码为{http_result}' if http_result else '失败'
        await test.finish(output)