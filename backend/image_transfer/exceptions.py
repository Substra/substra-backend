class ManifestNotFoundError(Exception):
    """The given docker image is not present in the
    registry. while it was specified in
    `docker_images_already_transferred`."""

    pass


class ManifestContentError(Exception):
    """The Manifest content must be str, bytes or bytearray."""

    pass
