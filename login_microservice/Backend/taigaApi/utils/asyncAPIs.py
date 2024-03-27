import asyncio
from aiohttp import ClientSession

async def execute_apis(url: str, queue: asyncio.Queue, headers):
    async with ClientSession() as session:
        try :
            request = session.get(url, headers=headers)
            async with request as response:
                if response.status > 400:
                    error_message = ""
                    if await '_error_message' in response.json:
                        error_message = await response.json()['_error_message']
                    raise Exception("Error while calling " + url + ". Status code: " + response.status + " " + error_message)
                result = await response.json()
                await queue.put(result)
        except Exception as e:
            print(e)



async def build_and_execute_apis(params, api_url, headers):
    # I'm using test server localhost, but you can use any url
    results = []
    queue = asyncio.Queue()
    async with asyncio.TaskGroup() as group:
        for i in params:
            group.create_task(execute_apis(api_url+str(i), queue, headers))

    while not queue.empty():
        results.append(await queue.get())



    return results

