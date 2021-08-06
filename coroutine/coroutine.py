# -*- coding: utf-8 -*-
import types
import uuid
import sys
import timer

def gen_guid():
    return uuid.uuid1()


class CallRpc(object):
    def __init__(self, rpc_method, *args):
        self.rpc_method = rpc_method
        self.args = args

class WaitFrame(object):
    def __init__(self, wait_frame):
        self.wait_frame = wait_frame

class CoWaitType(object):
    WAIT_TIME = 0
    WAIT_CO_TASK = 1
    WAIT_RPC = 2
    WAIT_FRAME = 3

class CoroutineTask(object):
    
    def __init__(self, guid, func):
        self.guid = guid
        self.func = func

        self.timer = None

        self.is_stop = False
        self.wait_type = None

class CoroutineManager(object):

    def __init__(self):
        self.coroutine_dict = {}
        self.co_wait_dict = {}


    def start_coroutine(self, co_task):
        self.coroutine_dict[co_task.guid] = co_task
        self.run_coroutine(co_task)
    
    def run_coroutine(self, task, ret=None):
        if task.is_stop:
            return
        try:
            yield_result = task.func.send(ret)
            self.handle_yield_result(yield_result, task)
        except StopIteration:
            self.handle_coroutine_finish(task.guid)
            self.coroutine_dict.pop(task.guid, None)
            task.is_stop = True
        except Exception:
            sys.excepthook(*sys.exc_info())

    def get_wait_type_from_result(self, yield_result):
        if isinstance(yield_result, (int, float)):
            return CoWaitType.WAIT_TIME
        elif isinstance(yield_result, types.GeneratorType):
            return CoWaitType.WAIT_CO_TASK
        elif isinstance(yield_result, CallRpc):
            return CoWaitType.WAIT_RPC
        elif isinstance(yield_result, WaitFrame):
            return CoWaitType.WAIT_FRAME

        return None

    def handle_yield_result(self, yield_result, co_task):
        wait_type = self.get_wait_type_from_result(yield_result)
        assert wait_type is not None, 'need wait type!!!'
        co_task.wait_type = wait_type
        if wait_type == CoWaitType.WAIT_TIME:
            wait_time = max(1, yield_result)
            timer.timer_mgr.add_timer(wait_time, self.yield_coroutine_time_end, co_task.guid)
        elif wait_type == CoWaitType.WAIT_FRAME:
            wait_frame = max(1, yield_result.wait_frame)
            timer.timer_mgr.add_frame_timer(wait_frame, self.yield_coroutine_time_end, co_task.guid)
        elif wait_type == CoWaitType.WAIT_CO_TASK:
            co_new_task = CoroutineTask(gen_guid(), yield_result)
            self.register_waiting_co_mapping(co_task.guid, co_new_task.guid)
            self.start_coroutine(co_new_task)
        elif wait_type == CoWaitType.WAIT_RPC:
            timer_obj = timer.timer_mgr.add_timer(5, self.yield_coroutine_time_end, co_task.guid)
            co_task.timer = timer_obj

            method = getattr(yield_result, 'rpc_method', None)
            if method:
                kwargs = {
                    'co_callback': str(co_task.guid)
                }
                method(*yield_result.args, **kwargs)
                self.register_waiting_co_mapping(co_task.guid, co_task.guid)

    def register_waiting_co_mapping(self, wait_co_guid, co_guid):
        self.co_wait_dict[co_guid] = wait_co_guid

    def handle_coroutine_finish(self, guid):
        if guid in self.co_wait_dict:
            co_resume_task = self.coroutine_dict.get(self.co_wait_dict[guid], None)
            self.co_wait_dict.pop(guid)
            if co_resume_task:
                self.run_coroutine(co_resume_task)

    def yield_coroutine_time_end(self, guid):
        co_task = self.coroutine_dict.get(guid)
        if not co_task or co_task.is_stop:
            return

        if co_task.timer:
            co_task.timer = None
        self.run_coroutine(co_task)


    def resume_coroutine(self, guid, ret_value=None):
        co_task = self.coroutine_dict.get(self.co_wait_dict.pop(guid, None), None)
        if co_task and co_task.timer:
            timer.timer_mgr.cancel(co_task.timer)
            co_task.timer = None
            self.run_coroutine(co_task, ret_value)





co_manager = CoroutineManager()




def coroutine(func):
    def wrapper(*args, **kwargs):
        # 普通函数
        if kwargs is not None:
            result = func(*args, **kwargs)
        else:
            result = func(*args)

        if not isinstance(result, types.GeneratorType):
            return result

        # 协程
        coroutine = CoroutineTask(gen_guid(), result)
        co_manager.start_coroutine(coroutine)
        return coroutine
    return wrapper



def wait_sec(time):
    yield time

