# Visual Studio Code

This document provides helpful resources when working on substra-backend in Visual Studio Code.

## Running unit tests from the Test Explorer

You can use the following settings to discover/run unit tests from the Test Explorer.

```json
{
    "python.testing.cwd": "${workspaceFolder}/backend",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "."
    ],
    "python.testing.unittestEnabled": false,
}
```

## Debugging unit tests

Use the following launch.json

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "purpose": ["debug-test"],
            "console": "integratedTerminal",
            "comment": "// we need --no-cov because https://github.com/microsoft/vscode-python/issues/693#issuecomment-926591721",
            "env": {
                "PYTEST_ADDOPTS": "--no-cov"
            },
        }
    ]
}
```
