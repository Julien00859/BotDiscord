from TheNumberOne import TheNumberOne, thenumberone
import asyncio
import re
import discord
from logging import getLogger
from operator import attrgetter

logger = getLogger(__name__)
groupe_channel = discord.utils.find(lambda channel: channel.name == "groupe", list(thenumberone.servers)[0].channels)
class_1T = discord.utils.find(lambda role: role.name == "1T", list(thenumberone.servers)[0].roles)
groups = {role.name.casefold(): role for role in list(thenumberone.servers)[0].roles if role.name in ["1TL1", "1TL2", "1TM1", "1TM2", "1TN1", "2T", "3T", "Ancien"]}

async def purge_groupe():
    await thenumberone.purge_from(groupe_channel)
    await thenumberone.send_message(groupe_channel, "Entrez vos classes séparée par une virgule. Exemple: `1TL2, 2T`")
    await thenumberone.send_message(groupe_channel, "Classes disponibles: " + ", ".join(sorted(groups.keys())))
asyncio.ensure_future(purge_groupe())

@TheNumberOne.forward("groupe", allow_commands=False)
async def group_reader(message):
    new = {groups[group] for group in re.split(",\s*", message.content.casefold()) if group in list(groups.keys())}
    if any(["1T" in n.name for n in new]):
        new.add(class_1T)
    if new:
        old = (set(groups.values()) | {class_1T}) & set(message.author.roles)
        logger.info(f"Change groups of {message.author} from {old} to {new}")
        await thenumberone.send_message(message.channel, "Les groupes de {} ont changé de: [{}] à: [{}]. N'oubliez pas de mettre votre prénom et nom en pseudo sur le serveur !".format(message.author.name, ", ".join(map(attrgetter("name"), old)), ", ".join(map(attrgetter("name"), new))))
        await asyncio.sleep(0.2)
        await thenumberone.remove_roles(message.author, *old)
        await asyncio.sleep(0.2)
        await thenumberone.add_roles(message.author, *new)
    else:
        msg = await thenumberone.send_message(message.channel, "Syntaxe incorrecte, merci d'entrer vos nouveaux groupes séparés par une virgule. Exemple: \"1T, 2T\"")
        await asyncio.sleep(5)
        await thenumberone.delete_message(msg)
    await thenumberone.delete_message(message)
