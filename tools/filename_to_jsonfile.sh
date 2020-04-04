#!/bin/bash
#
# Takes a directory of raw PNG transcriptions, where the filename is the meaning
# of the transcription. Changes the filenames so that they follow a numeric no
# meaning pattern, and stores the filename as a "meaning" in an associated json
# file, with the symbols key also present for future annotation.
# 
# That is, we have "eye.png", "ear.png", etc., and they are turned into
# "T001.png", "T002.png", along with "T001.json", "T002.json" with contents:
# { "meanings": [ "eye" ], "symbols": [] }
# 
# 2020-04-01 Antonio F. G. Sevilla <afgs@ucm.es>

DIR=$1 # Directory where files to be processed are

EXTENSION="png" # Extension for images
NUMBER=1 # Starting index for transcriptions

if [ -z "$DIR" ]; then
    echo "Usage: $0 [DATA DIRECTORY]"
    exit 1
fi

pushd "$DIR" >/dev/null

for file in *; do
    base="${file%.*}" # Remove extension
    base="${base%_*}" # Remove possible duplicate markers (eg eye_1.png -> eye)
    new_name=$(printf "%03d" $NUMBER)

    echo "{ \"meanings\": [ \"$base\" ], \"symbols\": [] }" >"$new_name.json"
    mv "$file" "$new_name.$EXTENSION"

    NUMBER=$((NUMBER+1))
done

popd >/dev/null
