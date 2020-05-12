# mcgap - Oriental Motor Control for MIRA

## About this app

This app controls 4 high-precision Oriental Motor stepper motors connected to the 36" telescope at the Oliver Observing Station, the research observatory for the Monterey Institute for Research in Astronomy. Authors: Gary Love and Eric Suchanek.


## How to run this app

(The following instructions apply to Posix/bash. Windows users should check
[here](https://docs.python.org/3/library/venv.html).)

First, clone this repository and open a terminal inside the root folder.

Create and activate a new virtual environment (recommended) by running
the following:

```bash
python3 -m venv myvenv
source myvenv/bin/activate
```

Install the requirements:

```bash
pip install -r requirements.txt
```
Run the app:

```bash
python app.py
```
