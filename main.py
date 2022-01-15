import os
from bot import Bot

if not 'TOKEN' in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

Bot().run(token=os.environ['TOKEN'])