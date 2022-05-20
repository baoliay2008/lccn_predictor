import yaml

yaml_config = None


def get_yaml_config():
    global yaml_config
    if yaml_config is None:
        with open('config.yaml', 'r') as yaml_file:
            yaml_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
    return yaml_config



