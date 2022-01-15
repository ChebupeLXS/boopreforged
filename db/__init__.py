from tortoise import Tortoise

TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['db.models'],
            'default_connection': 'master'
        }
    },
    'connections': {'master': 'sqlite://db/files/db.sqlite'}
}

async def init(reconnect=False, regenerate=False):
    if reconnect:
        await Tortoise.close_connections()
    await Tortoise.init(config=TORTOISE_ORM)
    if regenerate:
        await Tortoise.generate_schemas()