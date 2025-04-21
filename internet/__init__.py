from nonebot import get_plugin_config, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.adapters import Bot, Message, Event
from himibot.plugins.keep_safe import is_banned
import importlib, datetime, yaml, json, pycountry, gettext, aiohttp, asyncio
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from .config import Config
from playwright.async_api import async_playwright

__plugin_meta__ = PluginMetadata(
    name="internet",
    description="",
    usage="",
    config=Config,
)
whois = importlib.import_module('whois')
config = get_plugin_config(Config)
with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    config_dict = yaml.safe_load(f)
    http_proxy = config_dict['http_proxy'] if 'http_proxy' in config_dict else 'http://127.0.0.1:7890'

proxies= {'http': http_proxy, 'https': http_proxy}
no_proxies =  {'http': '', 'https': ''}

country_names = gettext.translation('iso3166-1', pycountry.LOCALES_DIR, languages=['zh_CN'])

async def http_test(url = 'http://cp.cloudflare.com', proxies = no_proxies):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, proxy=proxies.get('http') if proxies.get('http') else None, timeout=2) as response:
                return response.status
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False
    
async def blocked_without_proxy(url = 'https://www.v2ex.com/generate_204'):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=2) as response:
                return False
    except (aiohttp.ClientError, asyncio.TimeoutError):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, proxy=proxies.get('http'), timeout=2) as response:
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return 'Error'
        
async def extract_prefdomain_url(proxies = no_proxies):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.google.com', proxy=proxies.get('http') if proxies.get('http') else None, timeout=2) as response:
                content = await response.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
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
                return country_names.gettext(pycountry.countries.get(alpha_2='CN').name)
            else:
                return country_names.gettext(pycountry.countries.get(alpha_2=prefdom).common_name if pycountry.countries.get(alpha_2=prefdom).__dict__['_fields'].get('common_name') and prefdom != 'TW' else pycountry.countries.get(alpha_2=prefdom).name) if prefdom not in ('HK', 'MO') else country_names.gettext(pycountry.countries.get(alpha_2=prefdom).official_name)[:4]
    else:
        return None

async def raw_githubusercontent_speed_test(proxy_first = False):
    try:
        if not proxy_first:
            start = datetime.datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', timeout=1) as response:
                    end = datetime.datetime.now()
                    time_without_proxy = end - start
                    return time_without_proxy.total_seconds(), 'direct'
        else:
            start = datetime.datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', proxy=proxies.get('http'), timeout=1) as response:
                    end = datetime.datetime.now()
                    time_with_proxy = end - start
                    return time_with_proxy.total_seconds(), 'proxy'
    except (aiohttp.ClientError, asyncio.TimeoutError):
        try:
            if not proxy_first:
                start = datetime.datetime.now()
                async with aiohttp.ClientSession() as session:
                    async with session.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', proxy=proxies.get('http'), timeout=2) as response:
                        end = datetime.datetime.now()
                        time_with_proxy = end - start
                        return time_with_proxy.total_seconds(), 'proxy'
            else:
                start = datetime.datetime.now()
                async with aiohttp.ClientSession() as session:
                    async with session.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', timeout=2) as response:
                        end = datetime.datetime.now()
                        time_without_proxy = end - start
                        return time_without_proxy.total_seconds(), 'direct'
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False, False
        
async def get_ip_info(ip = '', use_proxy = True):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://ip-api.com/json/{ip}', 
                                 proxy=proxies.get('http') if use_proxy else None, 
                                 timeout=2) as response:
                ip_info = await response.json()
                return ip_info
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False

def domain_info(domain):
    status_mapping = {
        'clientDeleteProhibited': '客户端禁止删除',
        'clientTransferProhibited': '客户端禁止转移',
        'clientUpdateProhibited': '客户端禁止更新',
        'serverDeleteProhibited': '服务端禁止删除',
        'serverTransferProhibited': '服务端禁止转移',
        'serverUpdateProhibited': '服务端禁止更新',
        'ok': '正常'
    }

    try:
        query = whois.whois(domain)
        status_list = query['status'] if isinstance(query['status'], list) else [query['status']]
        friendly_status_list = []
        for status in status_list:
            if '(' in status and ')' in status:
                status_key = status.split('(')[1].split(')')[0]
            else:
                status_key = status.split()[-1]
            # 忽略包含 URL 的状态
            if 'http' in status_key or 'https' in status_key:
                continue
            friendly_status_list.append(status_mapping.get(status_key, status))
        friendly_status = '、'.join(list(set(friendly_status_list)))
        get_date_from_date_or_list = lambda date: date[0] if isinstance(date, list) else date
        query['creation_date'] = get_date_from_date_or_list(query['creation_date'])
        query['expiration_date'] = get_date_from_date_or_list(query['expiration_date'])
        for key in ['name', 'org', 'dnssec', 'registrar']:
            query[key] = query[key] if query.get(key) else '未知'

        area = f'{query["city"]}, {query["state"]}, {query["country"]}' if query.get('city') else f'{query["state"]}, {query["country"]}' if query.get('state') else f'{query["country"]}' if query.get('country') else None
        area = GoogleTranslator(source='auto', target='zh-CN', proxies=proxies).translate(area) if area else '未知'
        return f'注册商：{query["registrar"]}\n注册时间：{query["creation_date"]}\n过期时间：{query["expiration_date"]}\nDNS服务器数量：{len(query["name_servers"])}\n状态：{friendly_status}\nDNSSEC：{query["dnssec"]}\n所有者：{query["name"]}\n组织：{query["org"]}\n地域：{area}'
    except whois.parser.PywhoisError:
        return None

async def show_headers(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, 
                                  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}, 
                                  allow_redirects=True, 
                                  timeout=5) as response:
                headers = response.headers
                drop = ['Set-Cookie']
                for key in drop:
                    headers.pop(key, None)

                result = f'HTTP/{response.version.major}.{response.version.minor} {response.status} {response.reason}'
                for key, value in headers.items():
                    result += f'\n{key}: {value}'

                return result
    except asyncio.TimeoutError:
        return 'curl: (28) Operation timeout. The specified time-out period was reached.'
    except aiohttp.TooManyRedirects:
        return 'curl: (47) Too many redirects.'
    except aiohttp.ClientConnectorError as e:
        if 'Name or service not known' in str(e):
            return 'curl: (6) Could not resolve host.'
        elif 'Connection refused' in str(e):
            return 'curl: (7) Failed to connect to host or proxy.'
        else:
            return f'curl: (7) {e}'
    except aiohttp.ClientError as e:
        return f'curl: (56) Network error occurred: {e}'

async def get_academic_institute():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://login.cnki.net/TopLogin/api/loginapi/IpLoginFlush', 
                                 headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}, 
                                 timeout=2) as response:
                text = await response.text()
                result = json.loads(text[1:-1])
    except Exception:
        return False
    else:
        if result.get('IsSuccess'):
            return result.get('ShowName')
        else:
            return False

internet = CommandGroup('internet')
test = internet.command(tuple(), aliases={'net'})
ipinfo = internet.command('ip', aliases={'ip'})
whois_query = internet.command('whois', aliases={'lookup'})
show_headers_cmd = internet.command('headers', aliases={'curl -I'})
google_region = internet.command('google', aliases={'gcr'})
academic_institute = internet.command('institute', aliases={'institute'})

@test.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    if len(args) == 0:
        output = '成功的测试：'
        http_result = await http_test()
        https_result = await http_test('https://www.gstatic.com/generate_204')
        output += 'HTTP + HTTPS\n' if http_result and https_result else 'HTTP\n' if http_result else 'HTTPS\n' if https_result else '无\n'
        output += '网络：'
        output += '受限' if await blocked_without_proxy() else '自由'
        local_region, remote_region = await get_ip_info(use_proxy=False), await get_ip_info()
        output += f'（{GoogleTranslator(source='en', target='zh-CN', proxies=proxies).translate(f'{local_region["regionName"]}, {local_region["country"]} ').replace('中国', '') if local_region else '不可用'}'
        output += f'/{GoogleTranslator(source='en', target='zh-CN', proxies=proxies).translate(f'{remote_region["regionName"]}, {remote_region["country"]} ').replace('中国', '') if remote_region else '不可用'}）\n'
        output += 'Google 访问状况：'
        google_result = await blocked_without_proxy('https://www.google.com/generate_204')
        if google_result == 'Error':
            output += '失败'
        elif not google_result:
            output += f'直接'
            region = await extract_prefdomain_url()
            output += f'（{region}）' if region else ''
        else:
            output += f'间接'
            region = await extract_prefdomain_url(proxies)
            output += f'（{region}）' if region else ''
        output += '\nRaw GitHub User Content 访问测速：'
        speed, method = await raw_githubusercontent_speed_test()
        if speed and method:
            output += '直接' if method == 'direct' else '间接'
            output += f'连接用时{speed*1000:.2f}ms'
        else:
            output += '失败'
        institude = await get_academic_institute()
        if institude:
            output += f'\n学术机构：{institude}'
        await test.finish(output)
    else:
        url = args.extract_plain_text()
        if not url.startswith('http'):
            url = 'https://' + url
        output = f'URL 测试：\n'
        if await blocked_without_proxy(url) == 'Error':
            output += '失败\n'
        elif await blocked_without_proxy(url):
            output += 'BIC: Yes\n'
            http_result = await http_test(url, proxies)
            output += f'成功，状态码为{http_result}' if http_result else '失败'
        else:
            output += 'BIC: No\n'
            http_result = await http_test(url)
            output += f'成功，状态码为{http_result}' if http_result else '失败'
        await test.finish(output)

@ipinfo.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    ip = args.extract_plain_text()
    if ip == 'host':
        ip_info = await get_ip_info(use_proxy=False)
    elif ip == 'help':
        await ipinfo.finish(':ip host：获取本地 IP 信息\n:ip (IP 地址)：获取 IP 信息')
    elif ip:
        ip_info = await get_ip_info(ip)
    else:
        ip_info = await get_ip_info()
    if ip_info:
        if ip_info.get('message') == 'private range':
            await ipinfo.finish('私有 IP 地址是要问个啥。')
        output = f'IP: {ip}\n'
        output += f'地区：{ip_info["country"]} ({ip_info["countryCode"]})\n'
        output += f'城市：{ip_info["city"]}, {ip_info["regionName"]}\n'
        output += f'ISP：{ip_info["isp"]} ({ip_info["as"].split()[0]})\n'
        output += f'当地时区：{ip_info["timezone"]}\n'
        output += f'经纬度（粗略）：{ip_info["lat"]}, {ip_info["lon"]}'
        await ipinfo.finish(output)
    else:
        await ipinfo.finish('获取失败')

@whois_query.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    domain = args.extract_plain_text()
    if domain:
        output = domain_info(domain)
        if output:
            await whois_query.finish(output)
        else:
            await whois_query.finish('查询失败')
    else:
        await whois_query.finish('请输入域名')
        
@show_headers_cmd.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    url = args.extract_plain_text()
    if url:
        url = url if url.startswith('http') else 'http://' + url
        output = await show_headers(url)
        await show_headers_cmd.finish(output)
    else:
        await show_headers_cmd.finish('请输入 URL')

@google_region.handle()
async def handle(bot: Bot, event: Event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    google_access_status = await blocked_without_proxy('https://www.google.com/generate_204')
    if google_access_status == 'Error':
        await google_region.finish('无法连接到 Google。')
    elif not google_access_status:
        direct = True
    else:
        direct = False
    region = await extract_prefdomain_url(proxies) if not direct else await extract_prefdomain_url()
    if region:
        await google_region.finish(f'可以{"直接" if direct else "间接"}访问 Google，地区为 {region}。')
    else:
        await google_region.finish(f'可以{"直接" if direct else "间接"}访问 Google，目前正使用全球站点。')

@academic_institute.handle()
async def handle(bot: Bot, event: Event):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    institude = await get_academic_institute()
    if institude:
        await academic_institute.finish(f'我现在正使用{institude}的网络。')
    else:
        await academic_institute.finish('我现在不在学术机构内。')