# aries-acapy-plugins

This repository contains approved and tested plugins for Aries Cloudagent Python. This is to encourage collaboration and sharing of useful features not directly included in aca-py.

## Developer Notes

- Open devcontainer in VS Code
- Python and all dependencies will be loaded
- Poetry will be loaded and configured, dependencies will be installed
- Docker and Docker Compose will be available

IMPORTANT: docker-in-docker can be a little flaky, so if you encounter a messages such as: "Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?" you should probably reboot VS Code.

## Plugin Documentation

The development team should describe what the plugin does, any limitations (ex only in multitenant mode), any known issues interacting with other plugins, etc. Full documentation including a plugin_config sample should be provided.

This documentation should be provided in your plugin root as a README.md file. With at least a `Description` and `Configuration` section.

## Build and Run

A [Dockerfile](./basicmessage_storage/docker/Dockerfile) is provided to run integration tests. This image is not intended for production as it copies the plugin source and loads its dependencies (including ACA-Py) along with a simplistic ACA-Py configuration file: [default.yml](./basicmessage_storage/docker/default.yml).

## Run and Debug

In the devcontainer, we can run an ACA-Py instance with our plugin source loaded and set breakpoints for debug (see `launch.json`).

To run your ACA-Py code in debug mode, go to the `Run and Debug` view, select "Run/Debug Plugin" and click `Start Debugging (F5)`. Using [default.yml](./basicmessage_storage/docker/default.yml), your agent swagger is available at http://localhost:3001/api/doc.

## Testing

For the plugin to be accepted into this repo it must have adequate testing.

#### Unit Testing:

- There should be adequate unit testing coverage. A coverage report is created when `poetry run pytest` in ran from the devcontainer. A good mark to aim for is 90% but the quality of the tests on critical sections is more important than coverage percentage.
- Mocking can be challenging. Study the existing plugins in this repo and aca-py in general for good examples of mocks and fixtures.
- Put your unit tests in a tests folder in your plugin version path and name all files and test with the `test_` prefix.

#### Integration Testing:

- All plugins should have a suite of integration tests. The base suite will be created for your plugin after running the updater script
- See [integration tests](./basicmessage_storage/integration/README.md). You should have everything you need to start integration testing and a sample test will be provided.

## Deploy

For production use, plugins should be installed as libraries to an ACA-Py image.

This requires having a Dockerfile and a config file for your agent.

example Dockerfile:

```
FROM ghcr.io/hyperledger/aries-cloudagent-python:py3.9-0.10.3

USER root

# install plugins as binaries
RUN pip install git+https://github.com/hyperledger/aries-acapy-plugins@main#subdirectory=basicmessage_storage
RUN pip install git+https://github.com/hyperledger/aries-acapy-plugins@main#subdirectory=connection_update

USER $user
# copy configurations, choose at deploy time...
COPY ./configs configs

CMD ["aca-py"]
```

example config file (local single tenant):

```
auto-provision: true
label: plugins-agent

inbound-transport:
   - [http, 0.0.0.0, 9060]

outbound-transport: http

emit-new-didcomm-prefix: true
wallet-type: askar
wallet-storage-type: default

admin-insecure-mode: true

admin: [0.0.0.0, 9061]

endpoint: http://host.docker.internal:9060

genesis-url: https://indy.igrant.io/genesis

# Connections
debug-connections: true
auto-accept-invites: true
auto-accept-requests: true
auto-ping-connection: true
auto-respond-messages: true

log-level: info

# plugins
plugin:
  - basicmessage_storage.v1_0
  - connection_update.v1_0
```

Now you can deploy a agent with as many plugins as you want as long as they are decalred in your build config file and installed.

```
docker build -f <Dockerfile> --tag acapy_plugins .
docker run -it -p 9060:9060 -p 9061:9061 --rm acapy_plugins start --arg-file=<config-file> -->
```
