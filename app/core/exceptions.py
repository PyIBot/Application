class Error(Exception):
    """Base class for Madoka exceptions"""

    def __init__(self, msg=""):
        self.msg = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.msg

    __str__ = __repr__


class CommandManagerInitializedError(Error):
    """命令管理器未初始化"""

    def __init__(self):
        Error.__init__(self, "CommandManager is not initialized")


class CommandManagerAlreadyInitializedError(Error):
    """命令管理器重复初始化"""

    def __init__(self):
        Error.__init__(self, "CommandManager is already initialized")


class AppCoreNotInitializedError(Error):
    """核心模块未初始化"""

    def __init__(self):
        Error.__init__(self, "AppCore is not initialized")


class AppCoreAlreadyInitializedError(Error):
    """核心模块重复初始化"""

    def __init__(self):
        Error.__init__(self, "AppCore is already initialized")


class AriadneAlreadyLaunchedError(Error):
    """Ariadne重复启动"""

    def __init__(self):
        Error.__init__(self, "Ariadne is already launched")


class PluginNotInitializedError(Error):
    """插件未加载"""

    def __init(self, name):
        Error.__init__(self, "Plugin %r is not initialized" % name)
        self.name = name
        self.args = (name,)


class AsyncioTasksGetResultError(Error):
    """task得到结果提前结束"""

    def __init__(self, task):
        Error.__init__(self, "Task %r get result too early" % task)
        self.task = task
        self.args = (task,)


class FrequencyLimitError(Error):
    """频率限制"""

    pass


class FrequencyLimitExceededError(FrequencyLimitError):
    """群组请求超出负载权重限制"""

    def __init__(self, target, time: float):
        Error.__init__(self, "Frequency limit exceeded: %r, Remaining disable time: %.2f" % (target, time))
        self.target = target
        self.time = time
        self.args = (target, time)


class FrequencyLimitExceededDoNothingError(FrequencyLimitError):
    """请求者在黑名单中不作回应"""

    def __init__(self, target, time: float):
        Error.__init__(
            self, "Frequency limit exceeded and do nothing: %r, Remaining disable time: %.2f" % (target, time)
        )
        self.target = target
        self.limit = time
        self.args = (target, time)


class NonStandardPluginError(Error):
    """非标准插件"""

    def __init__(self, name):
        Error.__init__(self, "Plugin %r is not standard" % name)
        self.name = name
        self.args = (name,)


class PluginManagerInitializedError(Error):
    """插件管理器未初始化"""

    def __init__(self):
        Error.__init__(self, "PluginManager is not initialized")


class PluginManagerAlreadyInitializedError(Error):
    """插件管理器重复初始化"""

    def __init__(self):
        Error.__init__(self, "PluginManager is already initialized")


class RemotePluginNotFoundError(Error):
    """未在插件仓库找到该插件"""

    def __init__(self, name):
        Error.__init__(self, "Remote plugin %r not found" % name)
        self.name = name
        self.args = (name,)


class LocalPluginNotFoundError(Error):
    """未在本地找到该插件"""

    def __init__(self, name):
        Error.__init__(self, "Local plugin %r not found" % name)
        self.name = name
        self.args = (name,)


class DatabaseManagerInitializedError(Error):
    """数据库管理器未初始化"""

    def __init__(self):
        Error.__init__(self, "DatabaseManager is not initialized")


class DatabaseManagerAlreadyInitializedError(Error):
    """数据库管理器重复初始化"""

    def __init__(self):
        Error.__init__(self, "DatabaseManager is already initialized")


class ConfigInitializedError(Error):
    """配置文件未初始化"""

    def __init__(self):
        Error.__init__(self, "Config is not initialized")


class ConfigAlreadyInitializedError(Error):
    """配置文件重复初始化"""

    def __init__(self):
        Error.__init__(self, "Config is already initialized")


class PermissionDeniedError(Error):
    """对象无权限，结束处理"""

    def __init__(self, obj):
        Error.__init__(self, "Permission denied: %r" % obj)
        self.obj = obj
        self.args = (obj,)


class DependError(Error):
    pass


class NotActivatedError(DependError):
    def __init__(self, obj):
        Error.__init__(self, "%r is inactivated" % obj)
        self.obj = obj
        self.args = (obj,)


class BannedError(DependError):
    def __init__(self, obj):
        Error.__init__(self, "%r is banned" % obj)
        self.obj = obj
        self.args = (obj,)
