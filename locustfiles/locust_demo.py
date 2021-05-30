import json
import time
from locust import HttpUser, task, between, events, SequentialTaskSet, tag
from locust.runners import MasterRunner
from locust.contrib.fasthttp import FastHttpUser


# 请求：index
def index(l):
    l.client.get("/")

# 请求：stats
def stats(l):
    l.client.get("/stats/requests")


USER_CREDENTIALS = [
    ("user1", "password"),
    ("user2", "password"),
    ("user3", "password"),
]

# （1）定义了要执行的请求有哪些 >>> 场景1：login执行1次，addtitle执行10次
class FlashTask(SequentialTaskSet):  # 该类是TaskSet的子类，额外定义了执行请求的执行顺序，Sequential（有次序的）

    # 用户开始请求前，调用一次测试前置：on_start
    def on_start(self):
        user, passw = USER_CREDENTIALS.pop()
        self.client.post("/login", {"username": user, "password": passw})

    # 定义了一些特殊的请求
    tasks = [index, stats]

    token = None # 设置全局变量，login执行完成后，返回值给这里，供addtitle使用
    @task(1) # 先执行登录，执行1次 ，使用@task装饰器会更方便
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

# （2）定义了要发送请求的用户属性，例如：例如：要发送的网址、每次发送前后要做什么、第一个用户和第二个用户间隔时间、
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


    @tag("tag1")
    @task
    def hello_world(self):
        self.client.get("/hello")

    # tag是标签，
    # 场景1_执行tag1标记的任务：D:\GisLocust\locustfiles> locust -f locust_demo.py --tags tag1
    # 场景2_执行非tag1标记的任务：D:\GisLocust\locustfiles> locust -f locust_demo.py --exclude-tags tag1
    @tag("tag1", "tag2")
    @task(3)
    def view_items(self):
        for item_id in range(10):
            self.client.get(f"/item?id={item_id}", name="/item")
            time.sleep(1)

    tasks = [FlashTask]  # 要执行的任务是任务的类FlashTask，会有序执行该类下面的任务。


# 大并发情况下：fasthttpuser每秒处理5000个请求，httpruner每秒处理800个请求
class WebsiteUser(FastHttpUser):
    host = "http://127.0.0.1:8089"
    wait_time = between(2, 5)
    # some things you can configure on FastHttpUser
    # connection_timeout = 60.0
    # insecure = True
    # max_redirects = 5
    # max_retries = 1
    # network_timeout = 60.0

    @task
    def index(self):
        self.client.get("/")

    @task
    def stats(self):
        self.client.get("/stats/requests")