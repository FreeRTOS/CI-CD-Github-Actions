<div align="center">
  <p>
    <h3>Mosquitto MQTT Broker in GitHub Actions</h3>
  </p>
  <p>Start a Mosquitto message broker in your GitHub Actions.</p>
</div>

---

## Introduction

This GitHub Action starts a Mosquitto message broker as Docker container.
The published ports, TLS certificates and the Mosquitto configuration can be adjusted as needed.

This is useful when running tests against an MQTT broker.

## Usage

```yaml
name: Run tests

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Git checkout
        uses: actions/checkout@v2
  
      - name: Start Mosquitto
        uses: namoshek/mosquitto-github-action@v1
        with:
          version: '1.6'
          ports: '1883:1883 8883:8883'
          certificates: ${{ github.workspace }}/.ci/tls-certificates
          config: ${{ github.workspace }}/.ci/mosquitto.conf
          password-file: ${{ github.workspace}}/.ci/mosquitto.passwd
          container-name: 'mqtt'
  
      - run: test
```

Currently, the following parameters are supported:

| Parameter | Default  | Description |
|-----------|----------|-------------|
| `version` | `latest` | An image tag of the [eclipse-mosquitto](`https://hub.docker.com/_/eclipse-mosquitto`) Docker image |
| `ports`   | `1883:1883`   | Port mappings in a [host]:[container] format, delimited by spaces (example: "1883:1883 8883:8883") |
| `certificates` | -   | Absolute path to a directory containing certificate files which can be referenced in the config (the folder is mounted under `/mosquitto-certs` in the container) |
| `config`  | -        | Absolute path to a custom `mosquitto.conf` configuration file to use |
| `password-file` | -  | Absolute path to a custom `mosquitto.passwd` password file which will be mounted at `/mosquitto/config/mosquitto.passwd` |
| `container-name` | `mosquitto` | The name of the spawned Docker container (can be used as hostname when accessed from other containers) |

All parameters are optional. If no `certificates` are given, no volume is mounted. If no `config` is given, the default Mosquitto config is used.

## License

This action is published under the [MIT license](LICENSE).
