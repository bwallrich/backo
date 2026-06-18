import yaml

from backo.yaml.engine import YamlEngine

def init_data(path):
    with open(path, "w") as yaml_file:
        yaml_file.write(
            yaml.dump({"1": {"name": "pipo", "gid": 12, "description": "Example user"}})
        )

if __name__ == "__main__":
    init_data("test.yaml")

    yaml_engine = YamlEngine("test.yaml")
    print(yaml_engine.search("1"))
