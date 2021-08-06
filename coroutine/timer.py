# -*- coding: utf-8 -*-

import heapq
import time


class CallLater(object):
    def __init__(self, seconds, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

        self.cancelled = False
        self.timeout = time.time() + seconds

    def __le__(self, other):
        return self.timeout <= other.timeout

    def call(self):
        if callable(self.callback):
            self.callback(*self.args, **self.kwargs)

    def cancel(self):
        self.cancelled = True

class CallFrameLater(CallLater):
    def __init__(self, frame, callback, *args, **kwargs):
        super(CallFrameLater, self).__init__(frame, callback, *args, **kwargs)
        self.timeout = frame


class TimerManager(object):
    tasks = []
    wait_frame_tasks = []

    def add_timer(self, delay, func, *args, **kwargs):
        timer = CallLater(delay, func, *args, **kwargs)
        heapq.heappush(TimerManager.tasks, timer)
        return timer

    def add_frame_timer(self, delay, func, *args, **kwargs):
        timer = CallFrameLater(delay, func, *args, **kwargs)
        self.wait_frame_tasks.append(timer)
        return timer

    def update(self):
        now = time.time()
        while self.tasks and now >= TimerManager.tasks[0].timeout:
            call = heapq.heappop(TimerManager.tasks)
            if call.cancelled:
                continue
            call.call()

        del_list = []
        for wait_frame_task in self.wait_frame_tasks:
            wait_frame_task.timeout -= 1
            if wait_frame_task.timeout <= 0:
                wait_frame_task.call()
                del_list.append(wait_frame_task)

        for task in del_list:
            self.wait_frame_tasks.remove(task)



    def cancel(self, timer):
        if not (timer in TimerManager.tasks):
            return

        timer.cancel()
        return


timer_mgr = TimerManager()

