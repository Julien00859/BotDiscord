import discord
from collections import namedtuple, ChainMap
from enum import Enum
from config_parser import DISCORD_TOKEN, PREFIX
import asyncio
import logging
import re
from datetime import datetime
import signal
from typing import get_type_hints
from textwrap import dedent
from os import listdir
from os.path import isfile, sep

logger = logging.getLogger(__name__)

def cast_using_type_hints(type_hints: dict, kwargs: dict):
    """
    Given type_hints of function and some key word arguments,
    cast each kwarg with the type given by typehints
    except for None values, None in kwargs stay None
    """
    return {key: None if value is None else type_hints[key](value)
            for key, value in kwargs.items()}

Command = namedtuple("Command", ["channels", "roles", "regexp", "callback"])
EventType = Enum("EventType", ["MSG", "REACT-ADD", "REACT-DEL"])

class DispatcherMeta(type):
    """Dispatcher Pattern"""
    def __new__(mcs, name, bases, attrs):
        commands = ChainMap()
        forwards = ChainMap()
        maps = commands.maps
        maps_fw = forwards.maps
        for base in bases:
            if isinstance(base, DispatcherMeta):
                maps.extend(base.__commands__.maps)
                maps_fw.extend(base.__forwards__.maps)
        attrs["__commands__"] = commands
        attrs["__forwards__"] = forwards
        attrs["dispatcher"] = property(lambda obj: commands)
        attrs["forwarder"] = property(lambda obj: forwards)
        cls = super().__new__(mcs, name, bases, attrs)
        return cls

    def set_command(cls, channels, roles, pattern, callback):
        """Register a callback"""
        cmd_name = callback.__name__.strip("_")
        logger.info("Register command '%s' in %s usable by %s with%s for callback %s.", 
                        cmd_name,
                        f"channels {channels}" if channels is not None else "all channels",
                        f"roles {roles}" if roles is not None else "any role",
                        f" pattern '{pattern}'" if pattern is not None else "out pattern",
                        callback)
        
        cls.__commands__[cmd_name] = \
            Command(channels, roles, re.compile(pattern) if pattern else None, callback)

    def add_forward(cls, channels, callback):
        for channel in channels:
            logger.info(f"Forward message from {channel} to {callback}.")
            if channel not in cls.__forwards__:
                cls.__forwards__[channel] = []
            cls.__forwards__[channel].append(callback)

    def register(cls, channels, roles, pattern):
        """Decorator for register a command"""
        def wrapper(callback):
            cls.set_command(channels, roles, pattern, callback)
            return callback
        return wrapper

    def forward(cls, *channels):
        def wrapper(callback):
            cls.add_forward(channels, callback)
            return callback
        return wrapper

class TheNumberOne(discord.Client, metaclass=DispatcherMeta):
    def __init__(self):
        self.started_ = datetime.now()
        self.connected_ = False
        super().__init__()

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        logger.debug(f"Message from {message.author} on {message.channel}: {message.content}")
        for callback in self.forwarder.get(message.channel.name, []):
            logger.info(f"Forward to '{callback}'")
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        if message.content.startswith(PREFIX):
            cmd_name, *payload = message.content[1:].split(" ", 1)
        elif message.content.startswith(f"<@{self.user.id}>"):
            cmd_name, *payload = message.content.split(" ", 2)[1:]
        elif isinstance(message.channel, discord.Channel):
            return
        else:
            cmd_name, *payload = message.content.split(" ", 1)
        payload = payload[0] if payload else ""

        cmd = self.dispatcher.get(cmd_name)
        if not cmd:
            logger.warning(f"Command \"{cmd_name}\" not found.")
            await self.send_message(message.channel, f"<@{message.author.id}>, la commande \"{cmd_name}\" n'existe pas. Faites `!help` pour la liste des commandes.")
            return
        
        if cmd.channels is not None and message.channel.name not in cmd.channels:
            logger.warning(f"The command \"{cmd_name}\" is not available in the channel '{message.channels}'.")
            await self.send_message(message.channel, f"<@{message.author.id}>, la commande \"{cmd_name}\" n'est disponible que dans les salons suivants: {cmd.channels}.")
            return

        if cmd.roles is not None and discord.utils.find(lambda role: role.name in cmd.roles, message.author.roles) is None:
            logger.warning(f"The user {message.author} doesn't have the role needed to execute the command \"{cmd_name}\".")
            await self.send_message(message.channel, f"<@{message.author.id}>, la commande \"{cmd_name}\" n'est disponible que pour les roles suivants: {cmd.roles}.")
            return

        if cmd.regexp is not None:
            match = cmd.regexp.match(payload)
            if not match:
                logger.warning(f"Syntaxe error in command \"{cmd_name}\".")
                await self.send_message(message.channel, f"<@{message.author.id}>, la commande \"{cmd_name}\" n'a pas pu être exécutée car elle répond au pattern suivant: \"{cmd.regexp.pattern}\".")
                return

            kwargs = cast_using_type_hints(
                type_hints=get_type_hints(cmd.callback),
                kwargs=match.groupdict())
            logger.debug("Dispatch to '%s' with kwargs %s", cmd.callback.__name__, kwargs)
        else:
            logger.debug("Dispatch to '%s' with payload '%s'", cmd.callback.__name__, payload)

        try:
            if asyncio.iscoroutinefunction(cmd.callback):
                if cmd.regexp is not None:
                    await cmd.callback(message, **kwargs)
                else:
                    await cmd.callback(message, payload)
            elif cmd.regexp is not None:
                cmd.callback(message, **kwargs)
            else:
                cmd.callback(message, payload)
        except Exception as exc:
            logger.exception(f"Error in dispatched command.")
            await self.send_message(message.channel, "Internal error...")

    async def on_reaction_add(self, reaction, user):
        pass

    async def on_reaction_remove(self, reaction, user):
        pass

    async def on_ready(self):
        if not self.connected_:
            self.change_presence(game=discord.Game(name=f"{PREFIX}help", type=0))
            self.connected_ = True
            logger.info("Connected. Loading plugins...")
            try:
                for file in  listdir("plugins"):
                    if isfile(f"plugins{sep}{file}") and file != "__init__.py" and file.endswith(".py"):
                        logger.info(f"Load plugin '{file[:-3]}'")
                        __import__(f"plugins.{file[:-3]}")
                    else:
                        logger.info(f"Skip {file}")
            except:
                logger.exception(":(")

            logger.info("Done in %ss", (datetime.now() - self.started_).total_seconds())
            await self.purge_from(discord.utils.find(lambda chan: chan.name == "test-bot", list(self.servers)[0].channels), limit=200)

@TheNumberOne.register(None, None, None)
async def ping(message, payload):
    await thenumberone.send_message(message.channel, "Pong !")


@TheNumberOne.register(None, None, r"(?P<cmd_name>\S+)?")
async def help_(message, cmd_name: str = ""):
    if cmd_name:
        cmd = thenumberone.dispatcher.get(cmd_name)
        if cmd is None:
            await thenumberone.send_message(message.channel, f"<@{message.author.id}>, la commande \"{command}\" n'existe pas")
            return
        
        pattern_1 = cmd.regexp.pattern if cmd.regexp else "N/A"
        pattern_2 = cmd.regexp.pattern if cmd.regexp else ""
        payload = dedent(("""
        Commande **{0}**: %s
        Utilisable dans: {1}
        Utilisable par: {2}
        Pattern pour les arguments: {3}
        Utilisation: ```
        {4}{0}{5}```""".format(
            cmd_name,
            "*partout*" if cmd.channels is None else cmd.channels,
            "*tout le monde*" if cmd.roles is None else cmd.roles,
            "*N/A*" if cmd.regexp is None else f"`{cmd.regexp.pattern}`",
            PREFIX,
            "" if cmd.regexp is None else f" {cmd.regexp.pattern}"
        ) % (re.sub(r"\s+", " ", cmd.callback.__doc__) if cmd.callback.__doc__ else "<@!87605725857058816> a oublié de m'écrire une doc..."))[1:])
        await thenumberone.send_message(message.channel, payload)
    else:
        await thenumberone.send_message(message.channel, "Commandes disponibles: " + " ".join(thenumberone.dispatcher.keys()))


def start():
    logging.root.level = logging.NOTSET
    stdout = logging.StreamHandler()
    stdout.level = logging.DEBUG
    stdout.formatter = logging.Formatter(
        "[{levelname}] <{name}:{funcName}> {message}", style="{")
    logging.root.addHandler(stdout)

    logging.getLogger("discord").level = logging.WARNING
    logging.getLogger("websockets").level = logging.WARNING

    global thenumberone
    thenumberone = TheNumberOne()
    async def mainloop():
        await thenumberone.login(DISCORD_TOKEN)
        await thenumberone.connect()

    loop = asyncio.get_event_loop()
    stop = asyncio.Future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    asyncio.ensure_future(mainloop())

    logger.info("Connecting...")
    try:
        loop.run_until_complete(stop)
    except KeyboardInterrupt:
        logger.info("CTRL-C received, stopping.")
    except Exception as exc:
        logger.exception("Runtime error, stopping.")
    else:
        logger.info("SIGTERM received, stopping.")
    if not thenumberone.is_closed:
        loop.run_until_complete(thenumberone.logout())
    loop.close()
    logger.info("Stopped.")
