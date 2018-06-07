import uuid
from task import dao
d = dao.Dao()


class Result(object):

    def store(self):
        """
        入库方法
        :return:
        """
        pass

class Task:

    def __init__(self, id, group, **kwargs):
        self._t_id = id
        self._name = self.__class__.__name__
        self._group = group
        self._parent = kwargs.get('parent', None)
        # self.status = kwargs['status']
        self._task_info = kwargs.get('task_info', None)

    @property
    def parent(self):
        return self._parent

    @parent.setter

    def group(self, value):
        if self._group:
            raise Exception('')
        self._parent = value

    def genter_task(self, task):
        """
        开启子任务
        :param task:
        :return:
        """
        # TODO 如任务队列或任务数据库、平台统一调度任务
        # TODO 做一些统计比如任务量什么的？？
        task.parent = self._t_id
        d.insert(task)
        task.execute()

    def execute(self):
        """
        返回Result？
        :return:
        """
        pass

    def config(self):
        """
        配置项
        :return: 如{'speed': '30/m', 'debug'=True}
        """
        pass

    def store(self):
        """
        入库方法
        :return:
        """
        pass


class ListTask(Task):

    def execute(self):
        t_id = str(uuid.uuid1())
        self.genter_task(DetailTask(t_id, self._group,
                                    task_info={'key': 'value', 'sdfa': 'sdf', 'content': 'sdfasdfawesdfasfdjaiwefadkf' + t_id,}))


class DetailTask(Task):

    def execute(self):
        Task.execute(self)
        t_id = str(uuid.uuid1())
        self.genter_task(CommonTask(t_id, self._group,
                                    task_info={'key': 'value', 'sdfa': 'sdf',
                                               'content': 'sdfasdfawesdfasfdjaiwefadkf' + t_id}))
        for i in range(62):
            t_id = str(uuid.uuid1())
            self.genter_task(PicTask(t_id, self._group,
                                        task_info={'key': 'value', 'sdfa': 'sdf',
                                                   'content': 'sdfasdfawesdfasfdjaiwefadkf'}))


class CommonTask(Task):

    def execute(self):
        Task.execute(self)
        pass


class PicTask(Task):

    def execute(self):
        Task.execute(self)
        pass


