# System-Z Ownership
A set of scripts that parse and validate `service-info.yaml` files, update `.mention-bot` file to reflect the ownership and update _System-Z_.

## Usage


## Example (w/bash)
```
python ownership.py validate --root . --exclude native/
python ownership.py list --root . --exclude native/
python ownership.py mentionbot --root . --exclude native/
python ownership.py commit --root . -b master
python ownership.py synchronize --root . --exclude native/
```

## FAQ
