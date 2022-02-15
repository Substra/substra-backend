import argparse
import difflib
import pathlib
import re
import tempfile
from typing import Dict

FILE_PATH = pathlib.Path(__file__).parent.resolve()
SETTINGS_FOLDER = FILE_PATH / "../backend/backend/settings/"
DOC_PATH = FILE_PATH / "../docs/settings.md"
FILE_HEADER = """
<!-- This file is an auto-generated file, please do not edit manually. Instead you can run `make docs` to update it -->
# Connect setting
This file document all the settings of the connect application

These settings are configured through env variables.
They can be set in the [chart](../charts/substra-backend/README) through the `config` value.
"""
SUPPORTED_ENV_COMMANDS = [""]


def load_settings_from_file(filename: pathlib.Path) -> Dict[str, str]:
    """Opens a settings file an look for all the occurrences of os.getenv() or os.environ.get()

    Args:
        filename (pathlib.Path): Path of the settings file to scan

    Returns:
        Dict[str, str]: settings found with the structure [settings key, default value]
    """
    settings = {}
    with open(filename) as settings_file:
        for line in settings_file.readlines():
            try:
                # Regex explanation
                # - First we look for something that start with 'os.'
                # - Then we want either 'environ.get' or 'getenv' (note that we use a non-capturing group)
                # - Then we want '("'
                # - Then we want everything before the next '"' captured
                # We ignore the end of the function since maybe there is a default value, maybe not
                setting_name = re.search(r"os\.(?:environ\.get|getenv)\(\"(.+?)\"", line).group(1)
                # It's possible that there is no default value
            except AttributeError:
                setting_name = None
            try:
                # Regex explanation
                # - First we look for something that start with 'os.'
                # - Then we want either 'environ.get' or 'getenv' (note that we use a non-capturing group)
                # - Then we want '("'
                # - Then we want 'something",' and 1 or 0 space
                # - Then 1 or 0 quotes
                # - Then we want to capture everything except quotes because content may be python strings
                #     ("default") or just plain python (12 * 5)
                # - Then 1 or 0 quotes and a ')'
                default_value = re.search(r"os.(?:environ.get|getenv)\(\".*\", ?\"?([^\"]+?)\"?\)", line).group(1)
            except AttributeError:
                default_value = None
            if setting_name:
                settings[setting_name] = default_value

    return settings


def generate_doc(settings: Dict[str, Dict[str, str]], dest: pathlib.Path) -> None:
    """Generates a markdown documentation file of the settings

    Args:
        settings (Dict[str, Dict[str, str]]): settings to document with the structure
                                              Dict[section name, Dict[setting name, default value]]
        dest (pathlib.Path): destination file in which we should write the settings
    """
    with open(dest, "w") as settings_doc:
        settings_doc.write(FILE_HEADER)
        for section, values in settings.items():
            settings_doc.write(f"\n## {section} settings\n\n")

            settings_doc.write("| Setting | Default value |\n")
            settings_doc.write("| ---     | ---           |\n")

            for setting, default in sorted(values.items()):
                # Replace None with nil since None has a meaning in python
                default = "nil" if not default else default
                settings_doc.write(f"| `{setting}` | `{default}` |\n")


def parse_arguments() -> Dict[str, str]:
    parser = argparse.ArgumentParser(description="Generate settings documentation")
    parser.add_argument("--check", action="store_true")
    return vars(parser.parse_args())


def compare_content(generated: pathlib.Path, committed: pathlib.Path) -> bool:
    with open(generated, "r") as generated_file, open(committed, "r") as committed_file:
        generated_content = generated_file.read()
        committed_content = committed_file.read()

    if generated_content != committed_content:
        print("Committed settings documentation is not up to date.")
        print("To update run 'make docs'")
        for line in difflib.unified_diff(
            committed_content.splitlines(),
            generated_content.splitlines(),
            fromfile="committed",
            tofile="generated",
            lineterm="",
        ):
            print(line)
        return False
    return True


if __name__ == "__main__":
    args = parse_arguments()
    settings = {}
    settings["Global"] = load_settings_from_file(SETTINGS_FOLDER / "common.py")
    settings["Orchestrator"] = load_settings_from_file(SETTINGS_FOLDER / "deps/orchestrator.py")
    settings["Org"] = load_settings_from_file(SETTINGS_FOLDER / "deps/org.py")
    settings["CORS"] = load_settings_from_file(SETTINGS_FOLDER / "deps/cors.py")
    settings["Ledger"] = load_settings_from_file(SETTINGS_FOLDER / "deps/ledger.py")
    settings["Event app"] = load_settings_from_file(SETTINGS_FOLDER / "events/common.py")

    if args["check"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = pathlib.Path(tmpdir) / "settings.md"
            generate_doc(settings, tmp_file_path)
            is_identical = compare_content(tmp_file_path, DOC_PATH)
        if not is_identical:
            exit(1)
    else:
        generate_doc(settings, DOC_PATH)
