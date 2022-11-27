import yaml

yaml_config = None


def get_yaml_config():
    """
    Parse `config.yaml`
    :return:
    """
    global yaml_config
    if yaml_config is None:
        with open("config.yaml", "r") as yaml_file:
            yaml_config = yaml.safe_load(yaml_file)
    return yaml_config
