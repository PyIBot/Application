import asyncio

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain

from app.plugin.base import Plugin
from app.util.decorator import permission_required
from app.util.tools import isstartswith


class Admin(Plugin):
    entry = ['.admin']
    brief_help = '\r\n▶管理：admin'
    full_help = \
        '.admin\t仅限管理可用！\r\n' \
        '.admin ban [time] [qq]\t禁言用户\r\n' \
        '.admin unban [qq]\t解除禁言'
    hidden = True

    @permission_required(level='ADMIN')
    async def process(self):
        if not self.msg:
            self.print_help()
            return
        try:
            if isstartswith(self.msg[0], 'ban'):
                assert len(self.msg) == 3 and self.msg[1].isdigit()
                await self.app.mute(self.group, int(self.msg[2][1:]), int(self.msg[1]) * 60)
                self.resp = MessageChain.create([
                    Plain('禁言成功！')
                ])
            elif isstartswith(self.msg[0], 'unban'):
                assert len(self.msg) == 2 and self.msg[1][1:].isdigit()
                await self.app.unmute(self.group, int(self.msg[1][1:]))
                self.resp = MessageChain.create([
                    Plain('解除禁言成功！')
                ])
            else:
                self.args_error()
                return
        except PermissionError as e:
            print(e)
            self.exec_permission_error()
        except AssertionError as e:
            print(e)
            self.args_error()
        except Exception as e:
            print(e)
            self.unkown_error()


if __name__ == '__main__':
    a = Admin(MessageChain.create([Plain(
        '.admin ban 123'
    )]))
    asyncio.run(a.get_resp())
    print(a.resp)
