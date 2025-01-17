import asyncio
import uuid
from typing import Dict, Any, Callable, Awaitable

class BackgroundTaskManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}

    async def add_task(self, task_func: Callable[..., Awaitable[Any]], *args, **kwargs) -> str:
        """Add a new task to be processed in the background."""
        if not asyncio.iscoroutinefunction(task_func):
            raise ValueError("Task function must be a coroutine function.")
            
        task_id = str(uuid.uuid4())
        task = asyncio.create_task(self._run_task(task_id, task_func, *args, **kwargs))
        self.tasks[task_id] = task
        return task_id

    async def _run_task(self, task_id: str, task_func: Callable[..., Awaitable[Any]], *args, **kwargs):
        """Internal method to run the task and store the result."""
        try:
            result = await task_func(*args, **kwargs)
            self.results[task_id] = result
        except Exception as e:
            self.results[task_id] = e
        finally:
            del self.tasks[task_id]

    def get_result(self, task_id: str) -> Any:
        """Retrieve the result of a completed task."""
        if task_id in self.results:
            return self.results[task_id]
        elif task_id in self.tasks:
            raise ValueError("Task is still running.")
        else:
            raise ValueError("Task ID not found.")

    def is_task_done(self, task_id: str) -> bool:
        """Check if a task is done."""
        return task_id in self.results

    async def close(self):
        """Cancel all pending tasks and clean up."""
        if self.tasks:
            for task in self.tasks.values():
                task.cancel()
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
            self.tasks.clear()
            self.results.clear()


background_task = BackgroundTaskManager()

# # Example usage
# async def example_task(x: int, y: int) -> int:
#     await asyncio.sleep(2)  # Simulate a long-running task
#     return x + y

# async def main():
#     task_manager = BackgroundTaskManager()

#     # Add tasks to the manager
#     task_id1 = await task_manager.add_task(example_task, 1, 2)
#     task_id2 = await task_manager.add_task(example_task, 3, 4)

#     # Check if tasks are done
#     print(f"Task {task_id1} is done: {task_manager.is_task_done(task_id1)}")
#     print(f"Task {task_id2} is done: {task_manager.is_task_done(task_id2)}")

#     # Wait for tasks to complete
#     await asyncio.sleep(3)

#     # Retrieve results
#     print(f"Result of task {task_id1}: {task_manager.get_result(task_id1)}")
#     print(f"Result of task {task_id2}: {task_manager.get_result(task_id2)}")

#     # Clean up
#     await task_manager.close()

# # Run the example
# asyncio.run(main())