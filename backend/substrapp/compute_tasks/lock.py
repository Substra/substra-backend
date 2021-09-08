from substrapp.lock_local import lock_resource

MAX_TASK_DURATION = 24 * 60 * 60  # 1 day


def get_compute_plan_lock(compute_plan_key: str) -> None:
    """
    This lock serves multiple purposes:

    - *Prevent concurrent pod creation*
      Ensure concurrent compute tasks don't try to create the same pod at the same time

    - *Prevent resource starvation*.
      Prevent resource starvation: if two compute tasks from the same compute plan ran at the same time, they would
      compete for GPU/CPU/memory resources, and potentially fail.

    - *Adapt to task dir contraints*.
      The compute pod contains only one "task directory", which contains the working data for the current compute task.
      Running two compute tasks as part of the same compute plan concurrently would mean that the "task directory"
      would be used by two consumers. However, the "task directory" is designed to be used by a single consumer. For
      instance, out-models are stored in the "task directory": if 2 compute tasks belonging to the same compute plan
      run concurrently, one would overwrite the other's out-model.

    - *Make testtuple predictions available to the evaluation step*
      This is related to the previous point. Ensure that the "predict" and "evaluate" steps of a testtuple are run
      immediately one after the other. This is necessary because the "evaluate" step needs the pred.json file computed
      by the "predict" step. This file is stored in a shared folder (task_dir). Executing another compute task in
      between the two steps would result in the shared folder (task_dir) being altered, and `pred.json` potentially be
      lost or overwritten. The function `execute_compute_task` takes care of running both the "predict" and "evaluate"
      steps of the testtuple.

    - *Prevent the deletion compute plan resources while the compute plan is running*
      When the last compute task of a compute plan transitions to the "done" state, the compute plan itself transitions
      to the "done" state. As a result, an event is emitted to teardown (delete) the compute plan resources (pods,
      directories). If the AMQP event queue is busy, the execution of this teardown task might be delayed. If, in
      addition, the user adds a new compute task to the compute plan before the compute plan teardown task has been
      executed, the teardown of the compute plan might be executed _at the same time_ at the execution of the new
      compute task. In that scenario, the compute plan resources (pods, directories) should not be deleted until the
      compute task is completed. This lock ensures this is enforced.
    """
    return lock_resource("compute-plan", compute_plan_key, ttl=MAX_TASK_DURATION, timeout=MAX_TASK_DURATION)
