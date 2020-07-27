import time
import asyncio


async def do_almost_nothing(task_id):
    await asyncio.sleep(5)
    return task_id


async def main():
    num_tasks = 1000000
    tasks = []
    for task_id in range(num_tasks):
        tasks.append(asyncio.create_task(do_almost_nothing(task_id)))
    responses = await asyncio.gather(*tasks)
    print(len(responses))


asyncio.run(main())
