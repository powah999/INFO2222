#!/bin/bash

# This script deletes files in __pycache__ and database directories
# in terminal run chmod +x del.sh to give script permission
# in terminal run ./del.sh to execute script



directory="database"


if [ -d "$directory" ]; then

    rm -f "${directory}"/*
    echo "All files in ${directory} have been removed."
else
    echo "Directory ${directory} does not exist."
fi

directory="__pycache__"


if [ -d "$directory" ]; then

    rm -f "${directory}"/*
    echo "All files in ${directory} have been removed."
else
    echo "Directory ${directory} does not exist."
fi

directory="flask_session"


if [ -d "$directory" ]; then

    rm -f "${directory}"/*
    echo "All files in ${directory} have been removed."
else
    echo "Directory ${directory} does not exist."
fi