# HimiBot 插件列表

这是 HimiBot 的插件集合，包含了多个功能模块。

## 技术栈

HimiBot 是基于以下技术栈构建的：

### 核心框架
- NoneBot2 - Python异步机器人框架
- Python 3.8+

### 平台适配器
- OneBot V11 适配器 - QQ机器人协议
- Discord 适配器
- Telegram 适配器

### 主要插件依赖
- nonebot-plugin-apscheduler - 定时任务支持
- nonebot-plugin-alconna - 命令解析器

### 开发工具与库
- httpx - HTTP 客户端
- aiohttp - 异步HTTP客户端
- pydantic - 数据验证
- pyyaml - YAML配置支持
- openai - AI对话支持
- playwright - 网页自动化
- beautifulsoup4 - HTML解析

### 多语言支持
- deep-translator - 多语言翻译
- pycountry - 国家/地区代码

### 实用工具
- python-whois - 域名查询
- mcstatus - Minecraft服务器状态
- ping3 - 网络连接测试
- dnspython - DNS查询

## 插件列表

### ana
数据分析插件

### callme
- 用户昵称设置插件
- 支持用户自定义昵称
- 支持 Telegram 平台
- 命令：
  - `/callme <昵称>` - 设置昵称
  - `/callmewipe` - 清除昵称

### chat_summary
聊天摘要生成插件

### friendme
- 好友和群组管理插件
- 功能：
  - 好友请求处理
  - 群组邀请处理
  - 群成员验证
- 命令：
  - `friend` - 发送好友请求
  - `addgroup` - 添加群组（仅超级用户）

### locale
- 多语言支持插件
- 支持的语言：
  - 简体中文 (zh-cn)
  - 繁体中文 (zh-tw)
  - 英语(美国) (en-us)
  - 英语(英国) (en-gb)
  - 粤语 (zh-yue)
- 命令：
  - `locale` - 查看当前语言
  - `locale set` - 设置语言
  - `locale list` - 查看可用语言
  - `locale hello` - 测试当前语言
  - `locale reload` - 重载语言文件（仅超级用户）

### sign_in
签到系统插件

### userdata
- 用户数据管理插件
- 功能：
  - 用户信息存储
  - 数据库管理
  - 支持存储：
    - 用户昵称
    - 语言偏好
    - 代词设置
    - 货币数据
    - 权限等级
    - 签到数据

### whois
- 用户识别插件
- 功能：
  - 用户别名管理
  - 用户查找
- 命令：
  - `whois` - 查询用户信息
  - `whois list` - 列出所有用户别名
  - `whois add` - 添加用户别名（仅超级用户）
  - `whois remove` - 删除用户别名（仅超级用户）
  - `whois find` - 查找用户
  - `whois cue` - 发送查找请求

## 依赖

插件依赖包括：
- nonebot-adapter-onebot
- nonebot-adapter-discord
- nonebot-adapter-telegram
- nonebot-plugin-apscheduler
- nonebot-plugin-alconna
- httpx
- ping3
- openai
- pyyaml
- jsonpath
- deep-translator
- beautifulsoup4
- python-whois
- mcstatus
- playwright
- dnspython
- glotio-api
- pycountry
- tencentcloud-sdk-python
- aiohttp

## 许可证

本项目采用 GNU General Public License v3.0 开源许可证。