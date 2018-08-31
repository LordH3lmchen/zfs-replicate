"""Task Execution."""

import itertools
from typing import Dict, List

from .. import filesystem, optional, snapshot
from ..compress import Compression
from ..filesystem import FileSystem
from .type import Action, Task


def execute(
    remote: FileSystem,
    tasks: Dict[FileSystem, List[Task]],
    ssh_command: str,
    follow_delete: bool,
    compression: Compression,
) -> None:
    """Execute all tasks."""

    sorted_items = sorted(tasks.items(), key=lambda x: len(x[0].name.split("/")), reverse=True)

    for _, filesystem_tasks in sorted_items:
        action_tasks = {
            action: list(action_tasks)
            for action, action_tasks in itertools.groupby(filesystem_tasks, key=lambda x: x.action)
        }

        for action, a_tasks in action_tasks.items():
            if action == Action.CREATE:
                _create(a_tasks, ssh_command=ssh_command)
            elif action == Action.DESTROY:
                _destroy(a_tasks, ssh_command=ssh_command)
            elif action == Action.SEND:
                _send(remote, a_tasks, ssh_command=ssh_command, follow_delete=follow_delete, compression=compression)


def _create(tasks: List[Task], ssh_command: str) -> None:
    for task in tasks:
        filesystem.create(task.filesystem, ssh_command=ssh_command)


def _destroy(tasks: List[Task], ssh_command: str) -> None:
    for task in tasks:
        if task.snapshot is None:
            filesystem.destroy(task.filesystem, ssh_command=ssh_command)
        else:
            snapshot.destroy(task.snapshot, ssh_command=ssh_command)


def _send(
    remote: FileSystem, tasks: List[Task], ssh_command: str, follow_delete: bool, compression: Compression
) -> None:
    if tasks:
        snapshot.send(
            remote,
            optional.value(tasks[0].snapshot),
            ssh_command=ssh_command,
            compression=compression,
            follow_delete=follow_delete,
            previous=None,
        )

        for task, previous in zip(tasks[1:], tasks):
            snapshot.send(
                remote,
                optional.value(task.snapshot),
                ssh_command=ssh_command,
                compression=compression,
                follow_delete=follow_delete,
                previous=previous.snapshot,
            )
