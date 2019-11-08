[< Back to README](../README)

Linux user namespaces guide
---------------------------

This guide details how to enable user namespaces on Linux. This is a required step for running the substra backend.

On Linux systems, all the docker instances create files with `root` permissions.
To work correctly in a dev environment, we need the files created by our dockers to have the same rights as the ones we use to launch our celery tasks.
The celery tasks run dockers containers, these containers create files (models), the celery tasks manipulate these files.

To be able to make docker instances create files with the rights as the current Linux user, we need to modify some files as described [in this blog post](https://www.jujens.eu/posts/en/2017/Jul/02/docker-userns-remap/)

:warning: Modifying these files will override your global system configuration. Keep in mind it will apply to all the docker containers run on your machine.
Open/Create file `/etc/docker/daemon.json` with:

```
{
  "userns-remap": "USER"
}
```

Replace `USER` by your username (`echo $USER`). It is the user who will launch the celery tasks.

Then run this command to know the docker group:

```bash
$> getent group docker
docker:x:999:guillaume
```

`999` in my case.

Now modify the file `/etc/subuid` like:

```bash
guillaume:1000:1
guillaume:165536:65536
```

The first line should be added with the `1000` group (here the user is guillaume, replace it by yours).

And the file `/etc/subgid`:

```bash
guillaume:999:1
guillaume:165536:65536
```

The first line should be added with the docker group (999 in my case).

The final step is to re-download all the docker images. Go to the [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s) project and rerun the `./bootstrap.sh` script.
Do not forget to build the substra-model image as described in the step 9 of the [README](../README).