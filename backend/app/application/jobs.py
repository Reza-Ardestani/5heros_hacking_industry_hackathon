import logging
import re
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from uuid import uuid4


class BusyError(Exception):
    pass


class JobManager:
    def __init__(self, planner):
        self.planner = planner
        self.jobs = {}
        self.lock = Lock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="traffic-study")
        self.active = False

    def submit(self, scenario):
        with self.lock:
            if self.active:
                raise BusyError("A simulation is running; wait for it to finish")
            self.active = True
            job_id = uuid4().hex
            if len(self.jobs) >= 8:
                oldest = next(iter(self.jobs))
                del self.jobs[oldest]
            self.jobs[job_id] = {
                "id": job_id,
                "status": "running",
                "trace": [],
                "result": None,
                "error": None,
            }
        self.pool.submit(self._run, job_id, scenario)
        return job_id

    def _run(self, job_id, scenario):
        def emit(event):
            with self.lock:
                self.jobs[job_id]["trace"].append(event)

        try:
            result = self.planner.run(scenario, emit)
            with self.lock:
                self.jobs[job_id].update(status="completed", result=result)
        # Job boundary must record even unexpected failures and release its slot.
        except Exception as error:
            logging.getLogger(__name__).exception("Local simulation job failed")
            message = re.sub(r"/(?:Users|private|var|tmp)/[^\s'\"]+", "[local path]", str(error))
            with self.lock:
                self.jobs[job_id].update(status="failed", error=message[:1800])
        finally:
            with self.lock:
                self.active = False

    def get(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                return None
            return deepcopy(self.jobs[job_id])
