# REST API Connector Example

This example runs a small REST API server that manages virtual machines (VMs) deployed on an hypervisor.

Each VM has:

- `name`
- `image`

The API prefix for VMs is:

`http://localhost:12345/api/v1/hypervisor`

## Specific Dependencies

In addition to `backo` and its standard dependencies, this example requires:

- `pymongo`
- `flask_cors`

Install them in your environment:

```bash
pip install pymongo flask-cors
```

## Run The Example

From this folder (`examples/rest-api-connector/rest-api`):

```bash
python rest_api.py
```

The server starts on `0.0.0.0:12345` by default.

You can override settings from CLI:

```bash
python rest_api.py --config config.yaml --host 127.0.0.1 --port 12345 --log-level DEBUG
```

## Configuration (`config.yaml`)

`config.yaml` controls runtime paths, server binding, logging, and default image data.

### `data_dir`

```yaml
data_dir: "./data"
```

Directory where YAML collections are stored. At runtime the app creates this directory if needed.

### `server`

```yaml
server:
  host: "0.0.0.0"
  port: 12345
```

Network bind address and port for Flask.

### `logging`

```yaml
logging:
  level: "INFO"
```

Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).


## Data Model

### VM

```json
{
  "name": "vm-01",
  "image": "debian12"
}
```

`image` must reference an existing image in the `images` collection.

## Basic CRUD On VMs

Base URL: `http://localhost:12345/api/v1/hypervisor/vms`

### Create

```bash
curl -X POST http://localhost:12345/api/v1/hypervisor/vms \
  -H "Content-Type: application/json" \
  -d '{"name":"vm-01","image":"debian12"}'
```

### Read One

```bash
curl http://localhost:12345/api/v1/hypervisor/vms/<backo-id>
```

### Read Many

```bash
curl http://localhost:12345/api/v1/hypervisor/vms
```

### Update

```bash
curl -X PUT http://localhost:12345/api/v1/hypervisor/vms/<backo-id> \
  -H "Content-Type: application/json" \
  -d '{"name":"vm-01","image":"debian13"}'
```

### Delete

```bash
curl -X DELETE http://localhost:12345/api/v1/hypervisor/vms/<backo-id>
```

## Notes

- This is a minimal CRUD API intended as an example of a REST connector workflow.
- CORS is enabled with `origins=["*"]` for local development.
