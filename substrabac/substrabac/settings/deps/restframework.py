REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'libs.versioning.AcceptHeaderVersioningRequired',
    'ALLOWED_VERSIONS': ('1.0',),
    'DEFAULT_VERSION': '1.0',
}
