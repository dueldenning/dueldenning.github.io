from typing import List
from pathlib import Path
from json import loads
import logging

logger = logging.getLogger(__name__)

def load_file(path):
    with path.open() as file:
        logger.debug('Loading task: ' + str(path))
        return Task(path.stem, loads(file.read()))

class Task(object):
    def __init__(self, name, json):
        super(Task, self).__init__()
        logger.debug('Parsing task: ' + str(json))
        self.name = name
        self.overview = json['overview']
        self.draft = json['draft']
        self.briefs = json['briefs']
        self.options = json['options']

class Tasks(object):
    def __init__(self, folder) -> None:
        super(Tasks, self).__init__()
        folder = Path(folder)
        self._tasks = {path.stem: load_file(path) for path in folder.glob('*.json')}

    def exists(self, task_name) -> bool:
        return task_name in self._tasks

    def task_names(self) -> List[str]:
        return [name for name in self._tasks.keys()]

    def get(self, task_name) -> Task:
        return self._tasks[task_name]
