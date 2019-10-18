import tarfile
import zipfile

from django.core.exceptions import ValidationError

from django.utils.deconstruct import deconstructible


@deconstructible
class FileValidator(object):
    error_messages = {
        'open': ("Cannot handle this file object."),
        'compressed': ("Ensure this file is an archive (zip or tar.* compressed file)."),
        'docker': ("Ensure your archive contains a Dockerfile."),
        'file': ("Ensure your archive contains at least one python file."),
    }

    def validate_archive(self, files):
        if 'Dockerfile' not in files:
            raise ValidationError(self.error_messages['docker'])

        if len(files) < 2:
            raise ValidationError(self.error_messages['file'])

    def __call__(self, data):

        archive = None
        try:
            data.file.seek(0)
        except Exception:
            raise ValidationError(self.error_messages['open'])
        else:
            try:
                # is tarfile?
                archive = tarfile.open(fileobj=data.file)
            except tarfile.TarError:
                # is zipfile?
                if not zipfile.is_zipfile(data.file):
                    raise ValidationError(self.error_messages['compressed'])

                archive = zipfile.ZipFile(file=data.file)
                self.validate_archive(archive.namelist())
            else:
                self.validate_archive([x.name for x in archive.getmembers()])
            finally:
                if archive:
                    archive.close()
                else:
                    raise ValidationError(self.error_messages['open'])
