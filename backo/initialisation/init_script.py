"""
initialisation script
"""

import warnings
import json
import re
import sys
import os
import argparse
import questionary

from jinja2 import Environment, FileSystemLoader


warnings.filterwarnings("ignore")


# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import Dict, GenericType, List, Bool, String, ALL_TYPES

TYPE_AS_STRING = [t.__name__ for t in ALL_TYPES]
TYPE_AS_STRING.sort()


def dir_path(path):
    """check if the path is valid

    Args:
        path (_type_): _description_

    Raises:
        argparse.ArgumentTypeError: _description_

    Returns:
        _type_: _description_
    """
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")


# Setup argument parser
parser = argparse.ArgumentParser(description="Backo: initialisation tool.")
parser.add_argument("--expert", dest="expert", action="store_true")  # on/off flag
parser.add_argument("--dry_run", dest="dry", action="store_true")  # on/off flag
parser.add_argument(
    "repo", metavar="directory", type=dir_path, nargs="?", help="directory"
)

args = parser.parse_args()


class Init:
    """Create first backo organisation"""

    def __init__(self, prefix):
        """
        Constructor
        """
        self._prefix = prefix
        self._current_object = None

    def validate(self, v):
        """Validation of the user entry.
        It use obj.check(v) for that
        
        Args:
            v (Any): the value to check

        Returns:
            Bool|str: True if ok or the error message
        """
        try:
            self._current_object.check(v)
            return True
        except Exception as e: # pylint: disable= broad-exception-caught
            return str(e)

    def display_path(self, path: str):
        """display a breadcrump from the path ($.blabla)
        at the top of the terminal
        Args:
            path (str): a path
        """
        p = re.sub(r"^\$", self._prefix, path)
        p = re.sub(r"\.", ">", p)
        print("\033c\033[3J")
        questionary.print(f"{ p }>", style="bold fg:ansiyellow")

    def _get_description(self, schema: dict) -> str:
        """return the description if exists or just the path"""
        desc = schema.get("description", schema.get("path"))
        if desc is None:
            desc = schema.get("path")
        return desc

    def ask_field(self, obj: GenericType, schema: dict) -> None:  # pylint: disable=too-many-locals, too-many-branches
        """Main loop.

        Ask for a value. If a Dict or a List, go further.

        Args:
            obj (GenericType): The object to fill
            schema (dict): the schema of the object
        """
        self._current_object = obj

        desc = self._get_description(schema)

        default = schema.get("default")
        types = schema.get("types", False)
        exists = schema.get("exists", True)
        union = schema.get("union", True)
        rights = schema.get("rights", {"read": True, "modify": True})
        can_read = rights["read"]
        can_modify = rights["modify"]

        value = obj.get_value()

        if exists == False:
            return
        if can_read == False:
            return
        if can_modify == False:
            questionary.print(f"[RO] {desc} = {value}", style="italic")
            return

        # A dict, go down...
        if "Dict" in types:
            self.display_path(obj.path_name())
            for sub, sub_scheme in schema.get("sub_scheme", {}).items():
                self.ask_field(getattr(obj, sub), sub_scheme)
            return

        if "List" in types:
            # sub_type
            sub_type = schema.get("sub_type")
            sub_desc = self._get_description(sub_type)

            result = True
            while result is True:
                result = questionary.confirm(
                    message=f"Do you want to add a new {sub_desc} in {desc}",
                    default=True,
                ).ask()
                if result is True:
                    self.display_path(obj.path_name())
                    new_element = obj._type.copy()
                    new_element._parent = obj
                    new_element._attribute_name = f"[{len(obj)}]"
                    self.ask_field(new_element, sub_type)
                    obj.append(new_element)

            return

        my_default = value if value is not None else default
        question = None
        v = None
        if "Bool" in types:
            question = questionary.confirm(
                message=desc,
                default=my_default,
            )
            v = question.ask()
        elif "Int" in types:
            question = questionary.text(message=desc, default=my_default, validate=self.validate)
            v = int(question.ask())
        elif "Float" in types:
            question = questionary.text(message=desc, default=my_default, validate=self.validate)
            v = float(question.ask())
        else:
            if union is None:
                defa = "" if my_default is None else my_default
                question = questionary.text(
                    message=desc, default=defa, validate=self.validate
                )
            else:
                question = questionary.select(
                    message=desc, default=my_default, choices=union, validate=self.validate
                )
            v = question.ask()

        obj.set(v)


initiator = Init("Backo")


FIELD_MODEL = Dict(
    {
        "name": String(
            require=True, description="Name of the field", regexp=r"[A-z_-]+"
        ),
        "type": String(
            require=True,
            union=TYPE_AS_STRING,
            default="String",
            description="type of the field",
        ),
        "required": Bool(default=False, description="is the field required"),
        "default": String(description="a default value", can_read=args.expert),
    },
    description="field",
)

SELECTION_MODEL = Dict(
    {
        "name": String(
            require=True, description="Name of the selection", regexp=r"[A-z_-]+"
        ),
        "paths": List(
            String(required=True, description="path", regexp=r"^\$\..+"),
            description="paths list",
        ),
    },
    description="selection",
)

ACTION_MODEL = Dict(
    {
        "name": String(
            require=True, description="Name of the action", regexp=r"[A-z_-]+"
        ),
        "fields": List(FIELD_MODEL, default=[], description="action fields list"),
        "function_name": String(
            required=True, description="name of the function", regexp=r"[A-z_-]+"
        ),
    },
    description="selection",
)

COLLECTION_MODEL = Dict(
    {
        "name": String(
            require=True, description="Name of the collection", regexp=r"[A-z_-]+"
        ),
        "fields": List(FIELD_MODEL, default=[], description="fields list"),
        "selections": List(
            SELECTION_MODEL, default=[], description="selections", can_read=args.expert
        ),
        "actions": List(
            ACTION_MODEL, default=[], description="actions", can_read=args.expert
        ),
    },
    description="collection",
)

DB_MODEL = Dict(
    {
        "name": String(
            require=True, description="Name of the application", regexp=r"[A-z_-]+"
        ),
        "collections": List(
            COLLECTION_MODEL, default=[], description="the collections list"
        ),
    }
)


def backo_init() -> None:
    """Main run define in pyproject.toml
    """
    # Parse command line arguments
    my_db = DB_MODEL.copy()
    # initiator.display_path( my_db.path_name() )
    # initiator.ask_field( my_db, DB_MODEL.get_schema() )
    temp = my_db.get_encoded()

    print("----------------------------------------")
    print("Your configuration")
    print("----------------------------------------")
    print(json.dumps(temp, indent=2))
    print("----------------------------------------")
    resp = questionary.confirm(
        message="Is this configuration ok ?",
        default=True,
    ).ask()
    if resp is False:
        sys.exit()

    temp = {
        "name": "myApp",
        "collections": [
            {
                "name": "bd",
                "fields": [
                    {"name": "title", "type": "String", "required": True},
                    {"name": "pages", "type": "Int", "required": False},
                ],
                "selections": [
                    {"name": "suv", "paths": ["$.name", "$.title"]},
                ],
                "actions": [
                    {
                        "name": "toto",
                        "fields": [
                            {"name": "login", "type": "String", "required": True}
                        ],
                        "function_name": "test",
                    },
                ],
            },
            {
                "name": "readers",
                "fields": [{"name": "login", "type": "String", "required": True}],
            },
        ],
    }

    # Initialiser l'environnement avec un dossier de templates
    env = Environment(loader=FileSystemLoader("templates"))

    ## Building collections

    ## Building collection_set directory
    d = os.path.join(args.repo, "collections_set")
    if not os.path.exists(d):
        os.makedirs(d)

    template = env.get_template("collection.pytemplate")
    for collection in temp["collections"]:
        collection["app_name"] = temp["name"]
        rendered = template.render(collection)
        filename = os.path.join(d, f'{collection["name"]}.py')
        with open(filename, mode="w", encoding="utf-8") as outfile:
            outfile.write(rendered)

    template = env.get_template("__init__.pytemplate")
    rendered = template.render(temp)
    filename = os.path.join(d, "__init__.py")
    with open(filename, mode="w", encoding="utf-8") as outfile:
        outfile.write(rendered)

    template = env.get_template("backoffice.pytemplate")
    rendered = template.render(temp)
    filename = os.path.join(args.repo, "backoffice.py")
    with open(filename, mode="w", encoding="utf-8") as outfile:
        outfile.write(rendered)


if __name__ == "__main__":
    backo_init()
