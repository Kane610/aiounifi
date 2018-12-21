# aiounifi
Asynchronous library to communicate with Unifi Controller

## Acknowledgements
* Paulus Schoutsen (balloob) creator of aiohue which most of this code repository is modeled after.

#### Example
```python
import asyncio
import aiohttp

async def create():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        await run(session)


async def run(websession):
    ctl = aiounifi.controller.Controller('unifi.tld', websession,
                                         username='username',
                                         password='password')
    await ctl.login()
    await ctl.initialize()

    for device in ctl.clients:
        print('{}: {}'.format(ctl.clients[device].name, ctl.clients[device].ip))


def main():
    # Define an instance of an event loop
    loop = asyncio.get_event_loop()
    # Tell this event loop to run until all the tasks assigned
    # to it are complete. In this example just the execution of
    # our myCoroutine() coroutine.
    loop.run_until_complete(create())
    # Tidying up our loop by calling close()
    loop.close()


if __name__ == '__main__':
    main()
```
