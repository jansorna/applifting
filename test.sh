#!/usr/bin/env bash

chmod 777 "$PWD/test.sh"
ln -sf "$PWD/test.sh" .git/hooks/pre-push

echo '╔═══════════════════════╗'
echo '║executing pre-push hook║'
echo '╚═══════════════════════╝'

if [ -f "$PWD/venv/bin/activate" ]; then
    source $PWD/venv/bin/activate
fi

black --check --target-version py310 -l 120 --exclude venv .

if [ "$?" == 0 ]
then
    echo '╔════════════╗'
    echo '║black passed║'
    echo '╚════════════╝'
else
    echo '╔════════════════════════════════════════════════════╗'
    echo '║black failed so push blocked                        ║'
    echo '║please run:                                         ║'
    echo '║black --target-version py310 -l 120 --exclude venv .║'
    echo '╚════════════════════════════════════════════════════╝'
    exit 1
fi

pylint --rcfile=.pylintrc app/ applifting/

if [ "$?" == 0 ]
then
    echo '╔═════════════╗'
    echo '║pylint passed║'
    echo '╚═════════════╝'
else
    echo '╔═════════════════════════════╗'
    echo '║pylint failed so push blocked║'
    echo '╚═════════════════════════════╝'
    exit 1
fi

coverage run -m pytest

if [ "$?" == 0 ]
then
    echo '╔═══════════════════╗'
    echo '║pytest tests passed║'
    echo '╚═══════════════════╝'
else
    echo '╔═══════════════════════════════════╗'
    echo '║pytest tests failed so push blocked║'
    echo '╚═══════════════════════════════════╝'
    exit 1
fi

coverage report -m

coverage html

echo '╔═══════════════════════════════════╗'
echo '║pre-push hook executed successfully║'
echo '╚═══════════════════════════════════╝'
