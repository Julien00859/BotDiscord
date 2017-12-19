import asyncio
import discord
from logging import getLogger
from TheNumberOne import TheNumberOne, thenumberone
from operator import methodcaller, attrgetter

logger = getLogger(__name__)

numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
emojis = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
logger.debug(list(map(attrgetter("name"), thenumberone.get_all_emojis())))

@TheNumberOne.register(None, None, r"^\"(?P<question>.*?)\"\s*(?P<choix>((.*?)\/)+.*?)$")
async def vote(message, *_, question: str, choix: str):
    choix = list(filter(bool, map(methodcaller("strip"), choix.split("/"))))
    if len(choix) > 10:
        await thenumberone.send_message(message.channel, "Vous pouvez donner au maximum 10 choix.")
        return
    
    msg = await thenumberone.send_message(message.channel, "{}\n{}".format(question, "\n".join(map(lambda t: ":{}: {}".format(numbers[t[0]], t[1]), enumerate(choix)))))
    await asyncio.sleep(0.1)
    for idx in range(len(choix)):
        await thenumberone.add_reaction(msg, emojis[idx])
        await asyncio.sleep(0.1)
