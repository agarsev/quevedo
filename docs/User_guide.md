# Guide

Using quevedo repo with git and dvc

## Create repo

    quevedo -D dataset_name create

Modify config file

    cd dataset_name

From now on, everything run in the dataset directory

    git init
    git add -A .
    git commit -m "Created quevedo repository"
    dvc init
    git commit -m "Initialize DVC"

## Add data

    quevedo add_images -i image_directory -l logogram_set
    dvc add logograms/*
    git add logograms/logogram_set.dvc logograms/.gitignore
    git commit -m "Imported logograms"

## Automatically process the data

    mkdir scripts
    vim scripts/script_name.py
    quevedo run_script -s script_name -l logogram_set
    dvc add logograms

## Annotate the data

Modify config file with `quevedo config` to set the schema. Recommend keep
filename in meta tags.

    quevedo web
    dvc add logograms
    git commit -m "Annotated logograms"

## Extract graphemes

    quevedo extract -f logogram_set -t grapheme_set

## Split

    quevedo split -l B22 -p 100

## Prepare

    dvc run -n prepare_detect -d logograms -o networks/detect quevedo -N detect prepare
