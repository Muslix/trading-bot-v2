"""
Threading Manager for Trading Bot
Handles concurrent operations and improved performance
"""

import asyncio
import threading
import concurrent.futures
import logging
import time
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ThreadTask:
    """Thread task configuration"""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    interval: float = None  # For recurring tasks
    priority: int = 1  # 1=highest, 5=lowest


class ThreadingManager:
    """
    Manages threading for the trading bot to improve performance
    """
    
    def __init__(self, max_workers: int = 8):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.async_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.scheduled_tasks: List[ThreadTask] = []
        self.is_running = False
        
        # Performance metrics
        self.task_metrics = {
            'started': 0,
            'completed': 0,
            'failed': 0,
            'average_duration': 0.0
        }
        
        self.logger.info("🧵 Threading Manager initialized with %d max workers", max_workers)

    def submit_task(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit a one-time task to thread pool"""
        try:
            self.task_metrics['started'] += 1
            future = self.executor.submit(func, *args, **kwargs)
            
            # Add completion callback for metrics
            def on_complete(f):
                try:
                    result = f.result()
                    self.task_metrics['completed'] += 1
                    self.logger.debug("✅ Task completed: %s", func.__name__)
                except Exception as e:
                    self.task_metrics['failed'] += 1
                    self.logger.error("❌ Task failed: %s - %s", func.__name__, str(e))
            
            future.add_done_callback(on_complete)
            return future
            
        except Exception as e:
            self.logger.error("Failed to submit task %s: %s", func.__name__, str(e))
            self.task_metrics['failed'] += 1
            raise

    def submit_async_task(self, async_func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit an async task to async thread pool"""
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                loop.close()
        
        return self.async_executor.submit(run_async)

    def schedule_recurring_task(self, task: ThreadTask):
        """Schedule a recurring task"""
        if task.kwargs is None:
            task.kwargs = {}
        
        self.scheduled_tasks.append(task)
        self.logger.info("📅 Scheduled recurring task: %s (interval: %ss)", 
                        task.name, task.interval)

    def start_recurring_tasks(self):
        """Start all scheduled recurring tasks"""
        self.is_running = True
        
        for task in self.scheduled_tasks:
            if task.interval:
                thread = threading.Thread(
                    target=self._run_recurring_task,
                    args=(task,),
                    name=f"recurring_{task.name}",
                    daemon=True
                )
                thread.start()
                self.running_tasks[task.name] = thread
                self.logger.info("🔄 Started recurring task: %s", task.name)

    def _run_recurring_task(self, task: ThreadTask):
        """Run a recurring task in a loop"""
        while self.is_running:
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(task.func):
                    # Handle async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(task.func(*task.args, **task.kwargs))
                    finally:
                        loop.close()
                else:
                    # Handle sync function
                    task.func(*task.args, **task.kwargs)
                
                duration = time.time() - start_time
                self.task_metrics['completed'] += 1
                
                # Update average duration
                total_tasks = self.task_metrics['completed']
                current_avg = self.task_metrics['average_duration']
                self.task_metrics['average_duration'] = (
                    (current_avg * (total_tasks - 1) + duration) / total_tasks
                )
                
                self.logger.debug("✅ Recurring task %s completed in %.2fs", 
                                task.name, duration)
                
                # Sleep until next execution
                if task.interval:
                    time.sleep(max(0, task.interval - duration))
                    
            except Exception as e:
                self.task_metrics['failed'] += 1
                self.logger.error("❌ Recurring task %s failed: %s", task.name, str(e))
                time.sleep(5)  # Wait before retry

    def batch_execute(self, tasks: List[tuple], max_concurrent: int = None) -> List[Any]:
        """Execute multiple tasks concurrently with optional limit"""
        if max_concurrent is None:
            max_concurrent = self.max_workers
        
        results = []
        futures = []
        
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_futures = []
            
            for func, args, kwargs in batch:
                if kwargs is None:
                    kwargs = {}
                future = self.submit_task(func, *args, **kwargs)
                batch_futures.append(future)
            
            # Wait for this batch to complete
            for future in concurrent.futures.as_completed(batch_futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error("Batch task failed: %s", str(e))
                    results.append(None)
        
        return results

    def priority_execute(self, priority_tasks: Dict[int, List[tuple]]) -> Dict[int, List[Any]]:
        """Execute tasks based on priority (1=highest, 5=lowest)"""
        results = {}
        
        # Sort by priority (ascending, so 1 comes first)
        for priority in sorted(priority_tasks.keys()):
            tasks = priority_tasks[priority]
            self.logger.info("🎯 Executing %d tasks with priority %d", len(tasks), priority)
            results[priority] = self.batch_execute(tasks)
        
        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        active_threads = len([t for t in self.running_tasks.values() if t.is_alive()])
        
        return {
            'max_workers': self.max_workers,
            'active_threads': active_threads,
            'scheduled_tasks': len(self.scheduled_tasks),
            'tasks_started': self.task_metrics['started'],
            'tasks_completed': self.task_metrics['completed'],
            'tasks_failed': self.task_metrics['failed'],
            'success_rate': (
                self.task_metrics['completed'] / max(1, self.task_metrics['started']) * 100
            ),
            'average_task_duration': self.task_metrics['average_duration'],
            'is_running': self.is_running
        }

    def stop(self):
        """Stop all recurring tasks and shutdown thread pools"""
        self.logger.info("🛑 Stopping Threading Manager...")
        
        self.is_running = False
        
        # Wait for recurring tasks to stop
        for name, thread in self.running_tasks.items():
            if thread.is_alive():
                self.logger.debug("Waiting for task %s to stop...", name)
                thread.join(timeout=5)
        
        # Shutdown thread pools
        self.executor.shutdown(wait=True)
        self.async_executor.shutdown(wait=True)
        
        self.logger.info("✅ Threading Manager stopped")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on threading system"""
        metrics = self.get_metrics()
        
        health_status = {
            'healthy': True,
            'issues': [],
            'metrics': metrics
        }
        
        # Check for issues
        if metrics['tasks_failed'] > 0:
            failure_rate = metrics['tasks_failed'] / max(1, metrics['tasks_started']) * 100
            if failure_rate > 10:  # More than 10% failure rate
                health_status['healthy'] = False
                health_status['issues'].append(f"High failure rate: {failure_rate:.1f}%")
        
        if metrics['average_task_duration'] > 30:  # Tasks taking too long
            health_status['healthy'] = False
            health_status['issues'].append(f"Slow tasks: {metrics['average_task_duration']:.1f}s avg")
        
        dead_threads = [name for name, thread in self.running_tasks.items() 
                       if not thread.is_alive()]
        if dead_threads:
            health_status['issues'].append(f"Dead threads: {dead_threads}")
        
        return health_status


# Global instance
_threading_manager: Optional[ThreadingManager] = None

def get_threading_manager() -> ThreadingManager:
    """Get global threading manager instance"""
    global _threading_manager
    if _threading_manager is None:
        _threading_manager = ThreadingManager()
    return _threading_manager