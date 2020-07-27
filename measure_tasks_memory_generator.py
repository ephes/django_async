import time
# import uvloop
import asyncio


# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


#async def do_almost_nothing(task_id):
#    await asyncio.sleep(5)

async def do_almost_nothing():
    await asyncio.sleep(5)

async def main():
    num_tasks = 1000000
    #await asyncio.gather(*(do_almost_nothing(task_id) for task_id in range(num_tasks)))
    await asyncio.gather(*(do_almost_nothing() for task_id in range(num_tasks)))


asyncio.run(main())
