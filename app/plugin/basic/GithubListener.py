import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp.client
import requests
from arclet.alconna import Alconna, Subcommand, Option, Args, Arpamar, AnyUrl
from graia.ariadne.context import enter_context
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from loguru import logger

from app.api.doHttp import doHttpRequest
from app.core.command_manager import CommandManager
from app.core.config import Config
from app.core.settings import REPO
from app.plugin.base import Plugin, Scheduler
from app.util.control import Permission
from app.util.decorator import permission_required
from app.util.onlineConfig import save_config
from app.util.tools import app_path


class Module(Plugin):
    entry = 'github'
    brief_help = 'Github监听'
    manager: CommandManager = CommandManager.get_command_instance()

    @permission_required(level=Permission.GROUP_ADMIN)
    @manager(Alconna(
        headers=manager.headers,
        command=entry,
        options=[
            Subcommand('add', help_text='添加监听仓库', args=Args['repo': str, 'api': AnyUrl], options=[
                Option('--branch', alias='-b', args=Args['branch': str: '*'], help_text='指定监听的分支,使用 , 分隔, 默认监听全部分支')
            ]),
            Subcommand('modify', help_text='修改监听仓库配置', args=Args['repo': str], options=[
                Option('--name', alias='-n', args=Args['name': str], help_text='修改仓库名'),
                Option('--api', alias='-a', args=Args['api': AnyUrl], help_text='修改监听API'),
                Option('--branch', alias='-b', args=Args['branch': str: '*'], help_text='修改监听的分支, 使用 , 分隔, *: 监听所有分支')
            ]),
            Subcommand('remove', help_text='删除监听仓库', args=Args['repo': str]),
            Subcommand('list', help_text='列出当前群组所有监听仓库')
        ],
        help_text='Github监听, 仅管理可用'
    ))
    async def process(self, command: Arpamar, alc: Alconna):
        subcommand = command.subcommands
        other_args = command.other_args
        if not subcommand:
            return await self.print_help(alc.get_help())
        try:
            if subcommand.__contains__('add'):
                branch = other_args['branch'].replace('，', ',').split(',') if other_args.__contains__('branch') else [
                    '*']
                group_id = str(self.group.id)
                if REPO.__contains__(group_id) and other_args['repo'] in REPO[group_id]:
                    return MessageChain.create([Plain('添加失败，该仓库名已存在!')])
                repo_info = {other_args['repo']: {'api': other_args['api'], 'branch': branch}}
                if await save_config('repo', group_id, repo_info, model='add'):
                    if not REPO.__contains__(group_id):
                        REPO.update({group_id: {}})
                    REPO[group_id].update(repo_info)
                    return MessageChain.create([Plain("添加成功!")])
            elif subcommand.__contains__('modify'):
                group_id = str(self.group.id)
                repo = other_args['repo']
                if not other_args:
                    return self.args_error()
                if not REPO.__contains__(group_id) or repo not in REPO[group_id]:
                    return MessageChain.create([Plain('修改失败，该仓库名不存在!')])
                if other_args.__contains__('name'):
                    await save_config('repo', group_id, repo, model='remove')
                    await save_config('repo', group_id, {other_args['name']: REPO[group_id][repo]},
                                      model='add')
                    REPO[group_id][other_args['name']] = REPO[group_id].pop(repo)
                    repo = other_args['name']
                if other_args.__contains__('api'):
                    REPO[group_id][repo]['api'] = other_args['api']
                    await save_config('repo', group_id, {repo: REPO[group_id][repo]}, model='add')
                if other_args.__contains__('branch'):
                    REPO[group_id][repo]['branch'] = other_args['branch'].replace('，', ',').split(',')
                    await save_config('repo', group_id, {repo: REPO[group_id][repo]}, model='add')
                return MessageChain.create([Plain("修改成功!")])
            elif subcommand.__contains__('remove'):
                group_id = str(self.group.id)
                if not REPO.__contains__(group_id) or other_args['repo'] not in REPO[group_id]:
                    return MessageChain.create([Plain('删除失败，该仓库名不存在!')])
                await save_config('repo', group_id, other_args['repo'], model='remove')
                REPO[group_id].pop(other_args['repo'])
                return MessageChain.create([Plain("删除成功！")])
            elif subcommand.__contains__('list'):
                return MessageChain.create([Plain('\r\n'.join([
                    f"{name}: \r\napi: {info['api']}\r\nbranch: {info['branch']}" for name, info in
                    REPO[str(self.group.id)].items()]))])
            return self.args_error()
        except Exception as e:
            logger.exception(e)
            return self.unkown_error()


class Tasker(Scheduler):
    config = Config()
    cron = config.REPO_TIME

    async def process(self):
        if not self.config.ONLINE:  # 非 ONLINE 模式不监听仓库
            return
        if not self.config.REPO_ENABLE:  # 未开启仓库监听
            return
        logger.info('github_listener is running...')

        Path('./app/tmp/github').mkdir(parents=True, exist_ok=True)
        for group in REPO.keys():
            if os.path.exists(file := os.sep.join([app_path(), 'tmp', 'github', f'{group}.dat'])):
                with open(file, 'rb') as f:
                    obj = pickle.load(f)
            else:
                obj = {}
            for name, info in REPO[group].items():
                if not obj.__contains__(name):
                    obj.update({name: {}})
                try:
                    branches = await doHttpRequest(info['api'], 'get', 'JSON')
                    for branch in branches:
                        if info['branch'][0] != '*' and branch['name'] not in info['branch']:
                            continue
                        if not obj[name].__contains__(branch['name']):
                            obj[name].update({branch['name']: None})
                        if branch['commit']['sha'] != obj[name][branch['name']]:
                            obj[name][branch['name']] = branch['commit']['sha']
                            await message_push(self.app, group, name, branch)
                except aiohttp.client.ClientConnectorError:
                    logger.warning(f"获取仓库信息超时 - {info['api']}")
                except Exception as e:
                    logger.exception(f'获取仓库信息失败 - {e}')
            with open(file, 'wb') as f:
                pickle.dump(obj, f)


async def message_push(app, group, repo, branch):
    commit_info = requests.get(branch['commit']['url']).json()
    commit_time = datetime.strftime(
        datetime.strptime(commit_info['commit']['author']['date'],
                          "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8), '%Y-%m-%d %H:%M:%S')
    with enter_context(app=app):
        await app.sendGroupMessage(group, MessageChain.create([
            Plain('Recent Commits to ' + repo + ':' + branch['name']),
            Plain("\r\nCommit: " + commit_info['commit']['message']),
            Plain("\r\nAuthor: " + commit_info['commit']['author']['name']),
            Plain("\r\nUpdated: " + commit_time),
            Plain("\r\nLink: " + commit_info['html_url'])
        ]))
