from discord.ext.commands import CommandError

class CommandDisabled(CommandError):
    pass

class UserBlacklisted(CommandError):
    pass
