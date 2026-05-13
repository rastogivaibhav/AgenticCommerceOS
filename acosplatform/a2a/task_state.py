TASK_STATES = ['queued','started','completed','failed','cancelled','timed_out']
def next_state(current: str, requested: str) -> str:
    if requested not in TASK_STATES: raise ValueError('invalid_task_state')
    if current in {'completed','failed','cancelled','timed_out'} and requested != current:
        raise ValueError('terminal_state')
    return requested
