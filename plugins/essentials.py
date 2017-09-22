import asyncio
import discord
from logging import getLogger
from TheNumberOne import TheNumberOne, thenumberone

logger = getLogger(__name__)

@TheNumberOne.register(None, {"Admin Discord"}, r"(?P<text>.*)")
async def say(message, *_, text: str):
    """Fait parler le bot dans le salon courant"""
    await thenumberone.delete_message(message)
    await thenumberone.send_message(message.channel, text)

@TheNumberOne.register(None, {"Admin Discord"}, r"<#(?P<channel_id>[0-9]+)>\s+(?P<text>.*)")
async def sayin(message, *_, channel_id: str, text: str):
    """Fait parler le bot dans le salon spécifié"""
    channel = thenumberone.get_channel(channel_id)
    if channel is None:
        await thenumberone.send_message(message.channel, f"<@{message.author.id}>, le salon \"{channel_name}\" n'existe pas...")
        return
    await thenumberone.send_message(channel, text)

@TheNumberOne.register({"test-bot"}, {"Admin Discord"}, r"(?P<payload>.*)")
async def eval_(message, *_, payload: str):
    """Évalue le message en python avec le bot, asyncio et discord importés"""
    try:
        ret = eval(payload, {"thenumberone": thenumberone}, {"asyncio": asyncio, "discord": discord})
    except Exception as ex:
        logger.exception("Error while evaluating payload")
        await thenumberone.send_message(message.channel, str(ex))
    else:
        logger.info("%s", ret)
        await thenumberone.send_message(message.channel, ret)