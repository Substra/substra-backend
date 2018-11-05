from io import StringIO

from django.core.files.uploadedfile import InMemoryUploadedFile


def get_temporary_text_file(contents, filename):
    """
    Creates a temporary text file

    :param contents: contents of the file
    :param filename: name of the file
    :type contents: str
    :type filename: str
    """
    f = StringIO()
    flength = f.write(contents)
    text_file = InMemoryUploadedFile(f, None, filename, 'text', flength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


def get_sample_challenge():
    description_content = "Super challenge"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    metrics_content = "def metrics():\n\tpass"
    metrics_filename = "metrics.py"
    metrics = get_temporary_text_file(metrics_content, metrics_filename)

    return description, description_filename, metrics, metrics_filename


def get_sample_script():
    script_content = "import slidelib\n\ndef read():\n\tpass"
    script_filename = "script.py"
    script = get_temporary_text_file(script_content, script_filename)

    return script, script_filename


def get_sample_dataset():
    description_content = "description"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_data():
    file_content = "0\n1\n2"
    file_filename = "file.csv"
    file = get_temporary_text_file(file_content, file_filename)

    return file, file_filename


def get_sample_model():
    model_content = "0.1, 0.2, -1.0"
    model_filename = "model.bin"
    model = get_temporary_text_file(model_content, model_filename)

    return model, model_filename
