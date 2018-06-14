REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'libs.versioning.AcceptHeaderVersioningRequired',
    'ALLOWED_VERSIONS': ('0.0',),
    'DEFAULT_VERSION': '0.0',
}
