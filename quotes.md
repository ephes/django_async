# Quotes

> The people bashing threads are typically system programmers which have
> in mind use cases that the typical application programmer will never 
> encounter in her life. […] In 99% of the use cases an application 
> programmer is likely to run into, the simple pattern of spawning a
> bunch of independent threads and collecting the results in a queue is 
> everything one needs to know.[148]
> 
> — Michele Simionato Python deep thinker“ 
Auszug aus: Luciano Ramalho. „Fluent Python.“ Apple Books. 

> Concurrency: one of the most difficult topics in computer science
> (usually best avoided).[156]
> 
>  — David Beazley Python coach and mad scientist“
> Auszug aus: Luciano Ramalho. „Fluent Python.“ Apple Books. 

> „Python threads are great at doing nothing.”
>   — David Beazley Python coach and mad scientist
> 
> Auszug aus: Luciano Ramalho. „Fluent Python.“ Apple Books. [151]

> Concurrency is about dealing with lots of things at once.
> Parallelism is about doing lots of things at once.
> Not the same, but related. One is about structure, one is about
> execution. Concurrency provides a way to structure a solution to
> solve a problem that may (but not necessarily) be parallelizable.[157]
> 
> — Rob Pike Co-inventor of the Go language
> Auszug aus: Luciano Ramalho. „Fluent Python.“ Apple Books. 

> Threads require a lot of memory—about 8 MB per executing thread. On many
> computers, that amount of memory doesn’t matter for the 45 threads I’d need 
> in this example. But if the game grid had to grow to 10,000 cells, I would 
> need to create that many threads, which couldn’t even fit in the memory of 
> my machine. Running a thread per concurrent activity just won’t work.
> 
> Auszug aus: Brett Slatkin. „Effective Python: 90 Specific Ways to Write Better Python, Second Edition (Jochen Wersdörfer's Library).“ Apple Books. 

> The cost of starting a coroutine is a function call. Once a coroutine is
> active, it uses less than 1 KB of memory until it’s exhausted. Like 
> threads, coroutines are independent functions that can consume inputs from 
> their environment and produce resulting outputs. The difference is that 
> coroutines pause at each await expression and resume executing an async 
> function after the pending awaitable is resolved (similar to how yield 
> behaves in generators).
> 
> Auszug aus: Brett Slatkin. „Effective Python: 90 Specific Ways to Write 
> Better Python, Second Edition (Jochen Wersdörfer's Library).“ Apple Books. 

> Threads work fine, but the memory overhead for each OS thread—the kind that 
> Python uses—is on the order of megabytes, depending on the OS. We can’t 
> afford one thread per connection if we are handling thousands of 
> connections.
> 
> Auszug aus: Luciano Ramalho. „Fluent Python.“ Apple Books. 
