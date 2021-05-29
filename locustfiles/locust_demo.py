import json
import time
from locust import HttpUser, task, between, events, SequentialTaskSet
from locust.runners import MasterRunner


# 场景1：任务执行 > login执行1次，addtitle执行10次
class FlashTask(SequentialTaskSet):  # 该类定义了用户执行的任务的顺序。
    token = None # 设置全局变量，login执行完成后，返回值给这里，供addtitle使用
    @task(1) # 先执行登录，执行1次
    def login(self):
        data = {"username": "developer", "password": "developer"}
        # 打开文件、写入数据、关闭文件，一般用语法with as >>> 节约资源，处理完请求后悔自动关闭。
        with self.client.request(method='post', url='/prod-api/account/login', data=data) as response:
            res = self.login()
            d = json.loads(res.text)  # 将返回值转换为字典
            token = d.get("data").get("token")
            self.token = token # 实例化login的token，为上面的token,调用self.token就是token值

    @task(50) # 然后执行addtitle,执行50次
    def addtitle(self):
        data = {'xx': 'xxx'}
        headers = {'x-token': self.token,
                   'content-type': 'application/json;charset=UTF-8'}  # 一般需要加表单类型，不然会报错
        with self.client.request(method='post', url='/prod-api/arctile', json=data, headers=headers) as response:
            print(response.text)


class FlashUser(HttpUser):
    host = "http://flash-admin.enilv.cn" # 设置要测的ip地址
    wait_time = between(1, 3) # 设置等待时间，1到3秒之内

    @events.init.add_listener
    def on_locust_init(environment, **kwargs):
        if isinstance(environment.runner, MasterRunner):
            print("I'm on master node")
        else:
            print("I'm on a worker or standalone node")

    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        print("A new test is starting")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print("A new test is ending")

    # 用户开始请求前，调用一次测试前置：on_start
    def on_start(self):
        self.client.post("/login", json={"username":"foo", "password":"bar"})

    @task
    def hello_world(self):
        self.client.get("/hello")

    @task(3)
    def view_items(self):
        for item_id in range(10):
            self.client.get(f"/item?id={item_id}", name="/item")
            time.sleep(1)

    tasks = [FlashTask]  # 要执行的任务是任务的类FlashTask，会有序执行该类下面的任务。