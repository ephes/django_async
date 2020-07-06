import time

import concurrent.futures


def do_almost_nothing(thread_id):
    time.sleep(100)
    return thread_id


num_threads = 10000
results = []
s = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    future_to_function = {executor.submit(do_almost_nothing, thread_id): thread_id for thread_id in range(num_threads)}
    for future in concurrent.futures.as_completed(future_to_function):
        function = future_to_function[future]
        try:
            results.append(future.result())
        except Exception as exc:
            print('%r generated an exception: %s' % (function, exc))
elapsed = time.perf_counter() - s
print(f"do_almost_nothing executed in {elapsed:0.2f} seconds.")
