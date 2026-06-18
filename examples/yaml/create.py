from backo.yaml.engine import YamlEngine

if __name__ == "__main__":
    yaml_engine = YamlEngine("test.yaml")
    item_id = yaml_engine.create(
        {"name": "pipo", "gid": 12, "description": "Example user"}
    )
    print(f"Item {item_id} created.")
    print(yaml_engine.search(item_id))
