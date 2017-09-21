import asyncio
import discord
from logging import getLogger
from TheNumberOne import TheNumberOne, thenumberone

logger = getLogger(__name__)

@TheNumberOne.register({"test-bot"}, {"Admin Discord"}, None)
async def eval_(message, payload):
    try:
        ret = eval(payload, {"thenumberone": thenumberone}, {"discord": discord, "asyncio": asyncio})
    except Exception as ex:
        logger.exception("Error while evaluating payload")
        await thenumberone.send_message(message.channel, str(ex))
    else:
        logger.info("%s", ret)
        await thenumberone.send_message(message.channel, ret)

@TheNumberOne.register(None, {"Admin Discord"}, None)
async def say(message, payload):
    await thenumberone.send_message(message.channel, payload)

@TheNumberOne.register(None, {"Admin Discord"}, r"(?P<channel_name>\S+)\s+(?P<text>.*)")
async def sayin(message, channel_name: str, text: str):
    channel = discord.utils.find(lambda channel: channel.name == channel_name, list(thenumberone.servers)[0].channels)
    if channel is None:
        await thenumberone.send_message(message.channel, f"<@{message.auhtor.id}>, le salon \"{channel_name}\" n'existe pas...")
        return
    await thenumberone.send_message(channel, text)

