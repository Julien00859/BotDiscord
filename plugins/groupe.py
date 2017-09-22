from TheNumberOne import TheNumberOne, thenumberone
import asyncio
import re
import discord
from operator import attrgetter

groupe_channel = discord.utils.find(lambda channel: channel.name == "groupe", list(thenumberone.servers)[0].channels)
groups = {role.name: role for role in list(thenumberone.servers)[0].roles if role.name in ["1T", "2T", "3T"]}

async def purge_groupe():
    await thenumberone.purge_from(groupe_channel)
    await thenumberone.send_message(groupe_channel, "Entrez vos classes séparée par une virgule. Exemple: `1T, 2T` pour ceux en 1e et en 2e")
    await thenumberone.send_message(groupe_channel, "Classes disponibles: " + ", ".join(sorted(groups.keys())))
asyncio.ensure_future(purge_groupe())

@TheNumberOne.forward("groupe", allow_commands=False)
async def group_reader(message):
    new = {groups[group] for group in re.split(",\s*", message.content.upper()) if group in list(groups.keys())}
    if new:
        old = set(groups.values()) & set(message.author.roles)
        await thenumberone.send_message(message.channel, "Les groupes de {} ont changé de: [{}] à: [{}]".format(message.author.name, ", ".join(map(attrgetter("name"), old)), ", ".join(map(attrgetter("name"), new))))
        await asyncio.sleep(0.1)
        await thenumberone.remove_roles(message.author, *old)
        await thenumberone.add_roles(message.author, *new)
    else:
        msg = await thenumberone.send_message(message.channel, "Syntaxe incorrecte, merci d'entrer vos nouveaux groupes séparés par une virgule. Exemple: \"1T, 2T\"")
        await asyncio.sleep(5)
        await thenumberone.delete_message(msg)
    await thenumberone.delete_message(message)
