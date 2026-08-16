MOLRA
-----

Based on NGINX Unit 1.26.

Build
-----

On Debian or Ubuntu, install the build dependencies:

```sh
sudo apt update
sudo apt install -y build-essential curl php-dev libphp-embed
```

Build and install into the current directory:

```sh
./configure --prefix="$PWD" --user="$(id -un)" --group="$(id -gn)"
./configure php
make -j"$(nproc)"
make install
```

Configure PHP
-------------

Create a PHP application:

```sh
mkdir -p app
cat > app/index.php <<'PHP'
<?php
echo "Hello from MOLRA\n";
PHP
```

Start the server:

```sh
./sbin/unitd
```

Create and apply the configuration:

```sh
cat > config.json <<JSON
{
    "listeners": {
        "*:8080": {
            "pass": "applications/php"
        }
    },
    "applications": {
        "php": {
            "type": "php",
            "root": "$PWD/app",
            "index": "index.php"
        }
    }
}
JSON

curl -X PUT --data-binary @config.json \
    --unix-socket "$PWD/control.unit.sock" \
    http://localhost/config
```

Access
------

```sh
curl http://127.0.0.1:8080/
```
