import abc
import io

from zoloto_viewer.viewer.models import Project


class AbstractFileBuilder(abc.ABC):
    def __int__(self, bytes_buffer=False, extension='csv'):
        self.buffer = io.BytesIO() if bytes_buffer else io.StringIO()
        self.filename = ''
        self.extension = extension

    @abc.abstractmethod
    def build(self, project: 'Project'):
        pass
