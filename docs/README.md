cStock Documentation
====================

## Building the docs

First install sphinx if you haven't:

```
cd docs/
pip install -r requirements.txt
```

Then, to build the docs locally run:

```
make html
```

in this folder.

To view the docs in a browser, you can run:

```
cd _builds/html
python -m http.server
```

You can also automatically build the docs with `sphinx-autobuild`:

Install it:

```
pip install sphinx-autobuild
```

Then run:

```
sphinx-autobuild . _build/html/ --port 8001
```

## Hosting the docs

Docs are hosted on readthedocs and managed by Dimagi.
Credentials for the Dimagi account can be found in Keepass.
