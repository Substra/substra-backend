import os
import inspect
import json


EXCEPTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exceptions.json')

# Modules to inspect
os.environ['DJANGO_SETTINGS_MODULE'] = 'substrabac.settings.dev'


def exception_tree(cls, exceptions_classes):
    exceptions_classes.add(cls.__name__)
    for subcls in cls.__subclasses__():
        exception_tree(subcls, exceptions_classes)


def find_exception(module):
    # Exception classes in module
    exceptions = []
    exceptions = [ename for ename, eclass in inspect.getmembers(module, inspect.isclass)
                  if issubclass(eclass, BaseException)]

    # Exception classes in submodule
    for submodule in inspect.getmembers(module, inspect.ismodule):
        exceptions += [ename for ename, eclass in inspect.getmembers(module, inspect.isclass)
                       if issubclass(eclass, BaseException)]

    return set(exceptions)


if __name__ == '__main__':

    import docker.errors, requests.exceptions, celery.exceptions, tarfile, \
        django.core.exceptions, django.urls, django.db, django.http, django.db.transaction,\
        rest_framework.exceptions

    MODULES = [docker.errors, requests.exceptions, celery.exceptions, tarfile,
               django.core.exceptions, django.urls, django.db, django.http, django.db.transaction,
               rest_framework.exceptions]

    exceptions_classes = set()

    # Add exceptions from modules
    for errors_module in MODULES:
        exceptions_classes.update(find_exception(errors_module))

    # Add exceptions from python
    exception_tree(BaseException, exceptions_classes)

    exceptions_classes = sorted(exceptions_classes)

    if os.path.exists(EXCEPTION_PATH):
        # Append values to it
        json_exceptions = json.load(open(EXCEPTION_PATH))

        # get all new exceptions
        exceptions_classes = [e for e in exceptions_classes if e not in json_exceptions.keys()]

        # get the last value
        start_value = max(map(int, json_exceptions.values()))

        for code_exception, exception_name in enumerate(exceptions_classes, start=start_value + 1):
            json_exceptions[exception_name] = '%04d' % code_exception

        with open(EXCEPTION_PATH, 'w') as outfile:
            json.dump(json_exceptions, outfile, indent=4)

    else:
        # Generate the json exceptions
        json_exceptions = dict()
        for code_exception, exception_name in enumerate(exceptions_classes, start=1):
            json_exceptions[exception_name] = '%04d' % code_exception

        with open(EXCEPTION_PATH, 'w') as outfile:
            json.dump(json_exceptions, outfile, indent=4)
