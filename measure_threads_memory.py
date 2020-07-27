import time

import concurrent.futures


def do_almost_nothing(task_id):
    time.sleep(5)
    return task_id


num_tasks = 1000
results = []
s = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    future_to_function = {executor.submit(do_almost_nothing, task_id): task_id for task_id in range(num_tasks)}
    for future in concurrent.futures.as_completed(future_to_function):
        function = future_to_function[future]
        try:
            results.append(future.result())
        except Exception as exc:
            print('%r generated an exception: %s' % (function, exc))
elapsed = time.perf_counter() - s
print(f"do_almost_nothing executed in {elapsed:0.2f} seconds.")
