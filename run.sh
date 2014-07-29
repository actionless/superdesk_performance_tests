#!/bin/sh

which locust ||
echo "Did u entered virtualenv and installed all the dependencies from requirements.txt?

1) Create virtuelenv:
virtualenv -p python2 env

2) Enter virtualenv:
source ./env/bin/activate

3) Install dependencies:
pip install -r requirements.txt
" &&
exit 127

locust -f test.py --host localhost "$@"
