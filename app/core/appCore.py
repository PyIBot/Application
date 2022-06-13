import asyncio
import importlib
import sys
import threading
from asyncio.events import AbstractEventLoop
from types import ModuleType
from typing import List

from graia.ariadne.adapter import DefaultAdapter
from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.model import MiraiSession
from graia.broadcast import Broadcast
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler import GraiaScheduler
from loguru import logger
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from app.core.Exceptions import *
from app.core.commander import CommandDelegateManager
from app.core.config import Config
from app.core.initDB import InitDB
from app.core.plugins import PluginManager
from app.extend.power import power
from webapp.main import WebServer


class AppCore:
    __instance = None
    __first_init: bool = False
    __app: Ariadne = None
    __console: Console = None
    __loop: AbstractEventLoop = None
    __bcc: Broadcast = None
    __inc: InterruptControl = None
    __scheduler: GraiaScheduler = None
    __manager: CommandDelegateManager = None
    __plugins: PluginManager = None
    __database: InitDB = None
    __thread_pool = None
    __config: Config = None
    __launched: bool = False
    __group_handler_chain = {}

    def __new__(cls, config: Config):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, config: Config):
        if not self.__first_init:
            logger.info("Madoka is starting")
            logger.info("Initializing")
            self.__loop = asyncio.get_event_loop()
            self.__bcc = Broadcast(loop=self.__loop)
            self.__app = Ariadne(
                broadcast=self.__bcc,
                connect_info=DefaultAdapter(
                    broadcast=self.__bcc,
                    mirai_session=MiraiSession(
                        host=f'http://{config.LOGIN_HOST}:{config.LOGIN_PORT}',
                        verify_key=config.VERIFY_KEY,
                        account=config.LOGIN_QQ
                    ),
                    log=config.HEARTBEAT_LOG
                ),
                chat_log_config=False
            )
            self.__inc = InterruptControl(self.__bcc)
            self.__scheduler = GraiaScheduler(loop=self.__loop, broadcast=self.__bcc)
            self.__app.debug = False
            self.__config = config
            self.__console = Console(
                broadcast=self.__bcc,
                prompt=HTML('<split_1></split_1><madoka> Madoka </madoka><split_2></split_2> '),
                style=Style(
                    [
                        ('split_1', 'fg:#61afef'),
                        ('madoka', 'bg:#61afef fg:#ffffff'),
                        ('split_2', 'fg:#61afef'),
                    ]
                )
            )
            self.__manager = CommandDelegateManager()
            self.__plugins = PluginManager()
            self.__database = InitDB()
            AppCore.__first_init = True
            logger.info("Initialize end")
        else:
            raise AppCoreAlreadyInitialized()

    @classmethod
    def get_core_instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            raise AppCoreNotInitialized()

    def get_loop(self) -> AbstractEventLoop:
        if self.__loop:
            return self.__loop
        else:
            raise AppCoreNotInitialized()

    def get_app(self) -> Ariadne:
        if self.__app:
            return self.__app
        else:
            raise AppCoreNotInitialized()

    def get_bcc(self) -> Broadcast:
        if self.__bcc:
            return self.__bcc
        else:
            raise AppCoreNotInitialized()

    def get_inc(self):
        if self.__inc:
            return self.__inc
        else:
            raise AppCoreNotInitialized()

    def get_scheduler(self):
        if self.__scheduler:
            return self.__scheduler
        raise AppCoreNotInitialized()

    def get_console(self) -> Console:
        if self.__console:
            return self.__console
        else:
            raise AppCoreNotInitialized()

    def get_manager(self) -> CommandDelegateManager:
        if self.__manager:
            return self.__manager
        else:
            raise CommandManagerInitialized

    def get_plugin(self) -> List[ModuleType]:
        return self.__plugins.get_plugins()

    def get_config(self):
        return self.__config

    def launch(self):
        if not self.__launched:
            self.__app.launch_blocking()
            self.__launched = True
        else:
            raise AriadneAlreadyLaunched()

    def set_group_chain(self, chains: list):
        for chain in chains:
            self.__group_handler_chain[chain.__name__] = chain

    def get_group_chains(self):
        return self.__group_handler_chain

    def get_group_chain(self, chain_name: str):
        return self.__group_handler_chain[chain_name] if chain_name in self.__group_handler_chain else None

    async def bot_launch_init(self):
        try:
            await self.__plugins.loads_all_plugin()
            from app.extend.schedule import custom_schedule
            self.__loop.create_task(custom_schedule(self.__scheduler, self.__app))
            self.__database.start()
            if self.__config.WEBSERVER_ENABLE:
                threading.Thread(daemon=True, target=WebServer).start()
            self.__loop.create_task(power(self.__app, sys.argv))
            group_list = await self.__app.getGroupList()
            logger.info("本次启动活动群组如下：")
            for group in group_list:
                logger.info(f"群ID: {str(group.id).ljust(14)}群名: {group.name}")

            logger.success("WebServer is starting")
            importlib.__import__("app.core.eventCore")
            importlib.__import__("app.core.console")
        except Exception as e:
            logger.exception(e)
            exit()
