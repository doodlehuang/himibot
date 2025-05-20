import asyncio, aiohttp, datetime, yaml

old_data = None

with open('himibot/config.yml', 'r', encoding='utf-8') as f:
    http_proxy = yaml.safe_load(f).get('http_proxy')

class Version:
    def __init__(self, dict: dict):
        self.version = dict.get('id')
        self.type = dict.get('type')
        self.url = dict.get('url')
        self.release_time = datetime.datetime.fromisoformat(dict.get('releaseTime')) if dict.get('releaseTime') else None

class VersionList:
    def __init__(self, list: list):
        self.list = list
    def __iter__(self):
        return iter(self.list)
    def contains(self, version: Version):
        return any(v.version == version.version for v in self.list)
    def append(self, version):
        self.list.append(version)
    def versions(self):
        versions = []
        for version in self.list:
            versions.append(version.version) if version.version else None
        return versions

async def get_version_data():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://launchermeta.mojang.com/mc/game/version_manifest_v2.json', proxy=http_proxy) as response:
                data = await response.json()
                return True, data
    except Exception as e:
        return False, e

async def get_latest_version():
    state, data = await get_version_data()
    if not state:
        return False, None
    elif data is None:
        return False, None
    else:
        latest_versions = VersionList([])
        for version_type, version in data.get('latest').items():
            versions = data.get('versions')
            for v in versions:
                if v.get('id') == version:
                    latest_versions.append(Version(v))
                    continue
        return True, latest_versions

async def main():
    global old_data
    while True:
        # state, data = await get_latest_version()
        # print(data.list)
        # changed_versions = []
        # if state:
        #     old_data = data if old_data is None else old_data
        #     if data.versions() != old_data.versions():
        #         for version in data: changed_versions.append(version) if not old_data.contains(version) else None
        #     old_data = data
        # for version in changed_versions:
        #     print(f"Minecraft {version.version} {'快照' if version.type == 'snapshot' else '正式版'}于 {version.release_time.strftime('%Y-%m-%d %a %H:%M:%S')} UTC 发布")
        state, latest_versions = await get_latest_version()
        if state and latest_versions:
            message = '目前最新的 Minecraft 版本为'
            for version in latest_versions:
                message += f"\n{'快照' if version.type == 'snapshot' else '正式版'}: {version.version} ({version.release_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
            print(message)
        await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())