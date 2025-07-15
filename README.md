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
from backo import Item, DBYmlConnector, App
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
    Item(
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
    Item(
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
an_address = app.addrs.new() # A empty new object addr

# fill this object, save it in the "db", get a Id back
an_address.create({"name": "moon", "address": "far"})

# or more shorter
# an_address = app.addrs.create({"name": "moon", "address": "far"})

# Create a user with thos adress
u = app.users.create({"name": "bebert", "surname": "bebert", "addr": an_address._id})
```

### What happened ?

* When the user is created, the ```addr``` object in the db is modified to add the user._id in the field ```users``` to maintain the structure.

* Each object receive some meta datas. The first one is an _id (String()), callable by ```._id```

## Syntax

Please see [stricto](https://github.com/bwallrich/stricto).


[backo](https://github.com/bwallrich/backo) use [stricto](https://github.com/bwallrich/stricto) for structured description language.

### Item

```Item```is the main object in backo. It describe an object in the DB with all methodes for CRUD (CReate, Update, Delete)

A generic object is a [stricto](https://github.com/bwallrich/stricto) ```Dict()``` object.

```Item( description object , db connector )```

example :

```python
# Describe what is a 'cat'
cat = Item(
        {
            "name": String( required=True, default='Felix'),
            "address": String(),
            "age" : Int()
        },
        db_connector_for_cat)

# Add the cat object into the app object
app.add_collection( "cats", cat )
# similar : app.register_collection( "cats", cat )
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
author = Item({
    'name' : String(),
    'books' : RefsList( coll='book', field="$.autor" )
}, db_connector)

# A book is written by on author
book = Item({
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
This strategy is often used in *many-to-many* links. This strategy erase this reference on the reverse object

## Transactions

Soon

## CurrentUser

Soon

## Logs

Log system is based on [logging](https://docs.python.org/3/library/logging.html)

You must first design your logging system with handlers. Then write logs.

### sample use

```python
import logging
from backo import log_system

# To write all file to stderr
log_system.add_handler( log_system.set_streamhandler() )

# To write in a file
log_system.add_handler( log_system.set_filehandler("/var/log/mylog.log") )

# Set the level 
log_system.setLevel( logging.INFO )

# create your own sub logger with its specific logging level
log = log_system.get_or_create_logger("custom")
log.setLevel(loggind.DEBUG)

log.debug("hey this is my first debug message")

```

### advanced use

You can select a specific ```logger``` and modify it by adding/removing handlers and and changing its level.

```python
log = log_system.get_or_create_logger("custom")
log.setLevel(loggind.DEBUG)
log.addHandler ( my_own_handler )
# ...
```

### current loggers


Current availables loggers are :

| logger | description |
| - | - |
| app | The main App system |
| Item | The database itself (CRUD operations ) |
| ref | Ref and RefsList objects |
| transaction | transactions and roolback |
| yml | yaml database connector |




## Tests & co

```bash
# all tests
python -m unittest tests
# or for a specific test
python -m unittest tests.TestDict.test_simple_type

# reformat
python -m black .

# pylint
pylint $(git ls-files '*.py')

# coverage
coverage run -m unittest tests
coverage html # report under htmlcov/index.html

```
