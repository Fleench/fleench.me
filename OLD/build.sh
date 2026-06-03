#!/bin/bash
set -e

pip install -r requirements.txt --quiet
python gen.py build
