from backo.yaml.engine import YamlEngine

if __name__ == "__main__":
    yaml_engine = YamlEngine("test.yaml")
    item_id = yaml_engine.create(
        {"name": "pipo", "gid": 12, "description": "Example user"}
    )
    print(f"Item {item_id} created.")
    print(yaml_engine.search(item_id))

    item = yaml_engine.search(item_id)
    item["name"] = "molo"
    item["description"] = "Updated user"

    yaml_engine.save(item_id, item)
    print(f"Item {item_id} updated.")
    print(yaml_engine.search(item_id))
