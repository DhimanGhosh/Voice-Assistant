import config


def set_user_defined_parameters(params: dict):
    for param in list(params.keys()):
        config.param = params[param]


def setup():
    # Default values already set in 'Settings.py'

    cache_size = input('Desired CACHE_SIZE (in Mb): ')
    # Other parameters will come here

    params = dict()
    if cache_size:
        params['CACHE_SIZE'] = cache_size
        set_user_defined_parameters(params)
