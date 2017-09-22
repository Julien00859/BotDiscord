from TheNumberOne import TheNumberOne, thenumberone
import aiohttp
from bs4 import BeautifulSoup
from random import choice
from logging import getLogger
from collections import namedtuple, deque
from datetime import datetime, timedelta
import asyncio
from json import load as json_load
from html import unescape as html_unescape
from os.path import sep
from operator import itemgetter

Quote = namedtuple("Quote", ["author", "text"])

logger = getLogger(__name__)

dayly_quotes = []
quotes = deque([Quote(quote["author"], quote["text"]) for quote in json_load(open(f"plugins{sep}quotes.json", "r"))])

dayly_timer = datetime.now()
twenty_timer = datetime.now()

async def get_rss_items(url):
    async with thenumberone.http.session.get(url) as resp:
        assert resp.status == 200
        return BeautifulSoup(await resp.text(), "html.parser").find_all("item")

async def get_quotes():
    dayly_quotes.extend(map(lambda item: Quote(item.title.string.strip(), item.description.string.strip()[1:-1]),  await get_rss_items("http://feeds.feedburner.com/brainyquote/QUOTEBR")))
asyncio.ensure_future(get_quotes())

@TheNumberOne.register(None, None, r"(?P<author>.*)?")
async def quote(message, *_, author: str = ""):
    """Affiche une citation au hazard ou pour un auteur donné"""

    global dayly_timer, twenty_timer
    now = datetime.now()

    # Update dayly quotes everyday
    if now - dayly_timer >= timedelta(days=1):
        dayly_timer = now
        await get_quotes()

    # One quote allow each 20 minutes
    if now - twenty_timer < timedelta(seconds=5):
        await thenumberone.send_message(message.channel, "Je manque d'inspiration...")
        return
    twenty_timer = now

    # If an author is specified, select one randomly from that author
    if author:
        if author.casefold() in "chuck norris":
            async with thenumberone.http.session.get("http://www.chucknorrisfacts.fr/api/get?data=tri:alea;nb:3") as resp:
                assert resp.status == 200
                quote = Quote("Chuck Norris", html_unescape(max(await resp.json(), key=itemgetter("points"))["fact"]))

        else:
            author_quotes = list(filter(
                lambda quote: author.casefold() in quote.author.casefold(),
                quotes))
            if not author_quotes:
                await thenumberone.send_message(message.channel, "Je ne connais pas cet auteur.")
                return
            quote = choice(author_quotes)
    
    # If there are dayly_quotes left use one
    elif dayly_quotes:
        quote = dayly_quotes.pop()

    # Otherwise use our quotes
    else:
        quote = quotes.pop()
        quotes.appendleft(quote)
    await thenumberone.send_message(message.channel, f"{quote.author}: *{quote.text}*")