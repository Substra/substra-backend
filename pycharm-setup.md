[< Back to README](./README)

PyCharm setup
-------------

If you are using pycharm, you can very easily automate your servers and celery workers run configuration.

:warning: You have to specify the sources root of your django project:
![](assets/sources_root.png)

Enable Django support:
![](assets/django_enabled.png)

Use these configurations for easier debugging and productivity:

![](assets/conf.png)
![](assets/server_owkin.png)
![](assets/server_chunantes.png)
![](assets/celery owkin worker.png)
![](assets/celery owkin scheduler.png)
![](assets/celery chunantes worker.png)
![](assets/celery chunantes scheduler.png)
![](assets/celery_beat.png)

Do not hesitate to put breakpoints in your code. Even with periodic celery tasks and hit the `bug` button for launching your pre configurations.

You can even access directly to the databases (password is `backend` as described in the beginning of this document):
![](assets/database_owkin.png)
![](assets/database_owkin_challenges.png)

And for more convenience you can use the [multirun plugin](https://plugins.jetbrains.com/plugin/7248-multirun) from pycharm and configure it as:
![](assets/multirun.png)
