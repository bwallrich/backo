# Back Office Low Code (backo)


![release](https://img.shields.io/github/v/release/bwallrich/backo.svg?label=latest)


![pylint](https://img.shields.io/github/actions/workflow/status/bwallrich/backo/pylint.yml?label=linter) ![test](https://img.shields.io/github/actions/workflow/status/bwallrich/backo/test.yml?label=test)

Backo

The way to use is very simple, see [Quickstart](#quickstart) for a basic setup.

## What is backo


## Installation

```bash
pip install backo # (soon)
```

## Quickstart

Here is a sample with a DB (storage full in yaml file) with users and adresses reference

```mermaid
erDiagram
    User }o--|| Adresses : addr
    User {
        string name
        string surname
        bool male
        ref addr
    }
    Adresses {
        int orderNumber
        string name
        string adresse
        refs users
    }
```

Becomes in python with backo

```python
from backo import GenericDB, DBYmlConnector, App
from backo import Ref, RefsList, DeleteStrategy

# --- Storage for user
yml_users = DBYmlConnector(path="/tmp")
yml_users.generate_id = (
    lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
)
# --- Storage for addresses
yml_addr = DBYmlConnector(path="/tmp")
yml_addr.generate_id = lambda o: "Site_" + o.name.get_value()

# -- Description of the app
app = App("myApp")
app.add_collection(
    "users",
    GenericDB(
        {
            "name": String(),
            "surname": String(),
            "addr": Ref(coll="addrs", field="$.users", required=True),
            "male": Bool(default=True),
        },
        yml_users,
    ),
)
# --- DB for adresses
app.add_collection(
    "addrs",
    GenericDB(
        {
            "name": String(),
            "address": String(),
            "users": RefsList(
                coll="users", field="$.addr", ods=DeleteStrategy.MUST_BE_EMPTY
            ),
        },
        yml_addr,
    ),
)
```

Then usage :

```python
# Create a site, save it in the DB
addr = app.addrs.new() # A empty new object addr

# fill this object, save it in the "db", get a Id back
addr.create({"name": "moon", "address": "far"})

# Create a user in the site
u = app.users.new() # A empty new object user

# fill this object, save it in the "db", get a Id back
u.create({"name": "bebert", "surname": "bebert", "addr": si._id})
```

### What happened ?

* When the user is created, the ```addr``` object in the db is modified to add the user._id in the field ```users``` to maintain the structure.

* Each object receive some meta datas. The first one is an _id (String()), callable by ```._id```

## Syntax

Please see [stricto](https://github.com/bwallrich/stricto).


[backo](https://github.com/bwallrich/backo) use [stricto](https://github.com/bwallrich/stricto) for structured description language.

### GenericDB

```GenericDB```is the main object in backo. It describe an object in the DB with all methodes for CRUD (CReate, Update, Delete)

A generic object is a [stricto](https://github.com/bwallrich/stricto) ```Dict()``` object.

```GenericDB( description object , db connector )```

example :

```python
# Describe what is a 'cat'
cat = GenericDB(
        {
            "name": String( required=True, default='Felix'),
            "address": String(),
            "age" : Int()
        },
        db_connector,

# Add the cat object into the app object
app.add_collection( "cats", cat )
```

> [!IMPORTANT]  
> At this point, you don't care about ids. they will be added automatically by the db_connector.


| Method | Description |
| - | - |
| ```.create( data :dict )``` | Create an object into the DB with data in parameters. |
| ```.save()``` | save the object into the DB |
| ```.load( _id :str )``` | get the object with the _id from the DB |
| ```.delete()``` | delete the object |

each function raise errors in something goes wrong

### Ref and RefsList

A ```Ref()``` is a specific type for relation between collections ( aka *tables*).

#### Ref one to many

this is an example with *books* and *authors*

```python
# Authors write books
author = GenericDB({
    'name' : String(),
    'books' : RefsList( coll='book', field="$.autor" )
}, db_connector)

# A book is written by on author
book = GenericDB({
    ... # Some attibutes
    # one or zero to many
    author = Ref( coll='author', field="$.books" )
    # or one to many
    author = Ref( coll='author', field="$.books", required=True )
}, db_connector )
```

| Option for Ref | Default | Description |
| - | - | - |
| ```coll=``` | None | the collection to make the ref |
| ```table=``` | None | similar to ```coll``` |
| ```field=``` | None | The reverse field in the targeted collection (use [selector](https://github.com/bwallrich/stricto?tab=readme-ov-file#selectors) to target it) |
| ```rev=``` | None | similar to ```field``` |
| ```ods=``` | None | *On Delete Strategy* see [ods](#on-delete-strategy-ods)|

And all options availables in [stricto String()](https://github.com/bwallrich/stricto?tab=readme-ov-file#string) fields.


#### On Delete Strategy (ods)

ods define the behaviour of the database when a delete occure and the object contain some ```RefList```. For each  ```RefList```, you can define the strategy :

* ```DeleteStrategy.MUST_BE_EMPTY``` (by default)
This strategy oblige this RefList to be empty first. Otherwise, the delete wil be refused and an Error will be raised.

* ```DeleteStrategy.DELETE_REVERSES_TOO```
This strategy delete all reverse object too. can be dangerous.

* ```DeleteStrategy.CLEAN_REVERSES```
This strategy is often used in *many-to-many* links.
this strategy erase this reference on the reverse object

## Transactions

Soon

## CurrentUser

Soon

## Logs

Soon
