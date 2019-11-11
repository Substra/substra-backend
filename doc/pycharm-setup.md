[< Back to README](../README)

PyCharm setup
-------------

If you are using pycharm, you can very easily automate your servers and celery workers run configuration.

:warning: You have to specify the sources root of your django project:
![](./pycharm-screenshots/sources_root.png)

Enable Django support:
![](./pycharm-screenshots/django_enabled.png)

Use these configurations for easier debugging and productivity:

![](./pycharm-screenshots/conf.png)
![](./pycharm-screenshots/server_owkin.png)
![](./pycharm-screenshots/server_chunantes.png)
![](./pycharm-screenshots/celery owkin worker.png)
![](./pycharm-screenshots/celery owkin scheduler.png)
![](./pycharm-screenshots/celery chunantes worker.png)
![](./pycharm-screenshots/celery chunantes scheduler.png)
![](./pycharm-screenshots/celery_beat.png)

Do not hesitate to put breakpoints in your code. Even with periodic celery tasks and hit the `bug` button for launching your pre configurations.

You can even access directly to the databases (password is `backend` as described in the beginning of this document):
![](./pycharm-screenshots/database_owkin.png)
![](./pycharm-screenshots/database_owkin_challenges.png)

And for more convenience you can use the [multirun plugin](https://plugins.jetbrains.com/plugin/7248-multirun) from pycharm and configure it as:
![](./pycharm-screenshots/multirun.png)
