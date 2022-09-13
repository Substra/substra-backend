import argparse
import ast
import difflib
import pathlib
import tempfile
from dataclasses import dataclass
from os import name
from typing import Collection
from typing import Optional
from typing import Union

FILE_PATH = pathlib.Path(__file__).parent.resolve()
SETTINGS_FOLDER = FILE_PATH / "../backend/backend/settings/"
DOC_PATH = FILE_PATH / "../docs/settings.md"
FILE_HEADER = """
<!-- This file is an auto-generated file, please do not edit manually. Instead you can run `make docs` to update it -->
# Substra setting
This file document all the settings of the substra application

These settings are configured through env variables.
They can be set in the [chart](../charts/substra-backend/README) through the `config` value.
"""

TRUE_VALUES_HEADER_TEMPLATE = """
Accepted true values for `bool` are: {}; anything else is falsy.
"""

SUPPORTED_ENV_COMMANDS = [""]


def resolve_attribute_chain(node: Union[ast.Name, ast.Attribute]) -> Optional[str]:
    if isinstance(node, ast.Attribute):
        parent = resolve_attribute_chain(node.value)
        if parent is None:
            return None
        return parent + "." + node.attr
    elif isinstance(node, ast.Name):
        return node.id
    else:
        return None  # some expression that returns an identifier but we can't evaluate here


@dataclass
class Setting:
    type: str
    name: str
    default_value: Optional[str] = None
    default_value_comment: Optional[str] = None
    comment: str = ""


def load_settings_from_file(filename: pathlib.Path) -> list[Setting]:
    """Opens a settings file an look for all the occurrences of os.getenv() or os.environ.get()

    Args:
        filename (pathlib.Path): Path of the settings file to scan

    Returns:
        list[Setting]
    """
    settings = {}
    with open(filename) as settings_file:
        root = ast.parse(settings_file.read(), filename)
        settings_file.seek(0)
        settings_file_lines = settings_file.readlines()

        for node in ast.walk(root):
            for child in ast.iter_child_nodes(node):
                child._parent = node  # walk the entire tree to add a new _parent attribute

        def is_env_query(node: ast.AST) -> bool:
            if not (
                isinstance(node, ast.Call) and (len(node.args) in [1, 2]) and isinstance(node.args[0], ast.Constant)
            ):
                return False
            f_name = resolve_attribute_chain(node.func)
            return f_name in ["os.environ.get", "os.getenv"]

        for node in ast.walk(root):
            if not is_env_query(node):
                continue

            # try to guess the variable type by looking at the outer function call
            setting_type = "string"
            if isinstance(node._parent, ast.Call):
                parent_name = resolve_attribute_chain(node._parent.func)
                if parent_name == "int":
                    setting_type = "int"
                elif "bool" in parent_name:
                    setting_type = "bool"
                elif parent_name == "json.loads":
                    setting_type = "json"
            setting = Setting(setting_type, ast.literal_eval(node.args[0]))

            # get default value
            if len(node.args) > 1:
                try:
                    setting.default_value = ast.literal_eval(node.args[1])
                except ValueError:
                    # default value is an expression, evaluate it to get a valid input
                    setting.default_value = eval(ast.unparse(node.args[1]))  # nosec
                    setting.default_value_comment = ast.unparse(node.args[1])

            # get same-line comment
            if node.lineno and "#" in settings_file_lines[node.lineno - 1]:
                setting.comment = settings_file_lines[node.lineno - 1].split("#", 1)[1].strip()

            # get previous-line comment
            previous_line = settings_file_lines[node.lineno - 2].strip()
            comment_header = f"# @{setting.name}:"
            if previous_line.startswith(comment_header):
                setting.comment = previous_line.removeprefix(comment_header).strip()

            settings[setting.name] = setting  # use dict to eliminate duplicates

        return list(settings.values())


def load_true_values_from_file(filename: pathlib.Path):
    """
    Open settings file and get the value of a TRUE_VALUES constant
    """
    with open(filename) as settings_file:
        root = ast.parse(settings_file.read(), filename)
        for node in ast.walk(root):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "TRUE_VALUES"
            ):
                true_values = eval(ast.unparse(node.value))  # nosec
                return sorted({str(it) for it in true_values}, key=lambda it: (it.lower(), it))
                # sets are by definition unordered but we don't want values jumping around
                # we also want to eliminate duplicate values (eg 1-the-int vs 1-the-string)
    return None


def generate_doc(settings_by_section: dict[str, list[Setting]], true_values: Collection, dest: pathlib.Path) -> None:
    """Generates a markdown documentation file of the settings

    Args:
        settings_by_section: list of settings per section
        true_values: strings acceptable as boolean "true"
        dest (pathlib.Path): destination file in which we should write the settings
    """
    with open(dest, "w") as settings_doc:
        settings_doc.write(FILE_HEADER)
        settings_doc.write(TRUE_VALUES_HEADER_TEMPLATE.format(", ".join([f"`{it}`" for it in true_values])))
        for section, settings in settings_by_section.items():
            settings_doc.write(f"\n## {section} settings\n\n")

            settings_doc.write("| Type | Setting | Default value | Comment |\n")
            settings_doc.write("|------|---------|---------------|---------|\n")

            for setting in sorted(settings, key=lambda setting: setting.name):
                # Replace None with nil since None has a meaning in python
                default = "nil" if setting.default_value is None else f"`{setting.default_value}`"
                default_value_comment = f" (`{setting.default_value_comment}`)" if setting.default_value_comment else ""
                settings_doc.write(
                    f"| {setting.type} | `{setting.name}` | {default}{default_value_comment} | {setting.comment} |\n"
                )


def parse_arguments() -> dict[str, str]:
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
    settings["Worker event app"] = load_settings_from_file(SETTINGS_FOLDER / "worker/events/common.py")
    settings["API event app"] = load_settings_from_file(SETTINGS_FOLDER / "api/events/common.py")

    true_values = load_true_values_from_file(SETTINGS_FOLDER / "common.py")

    if args["check"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = pathlib.Path(tmpdir) / "settings.md"
            generate_doc(settings, true_values, tmp_file_path)
            is_identical = compare_content(tmp_file_path, DOC_PATH)
        if not is_identical:
            exit(1)
    else:
        generate_doc(settings, true_values, DOC_PATH)
