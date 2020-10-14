#!/bin/bash
cd $1
for i in *.pdf; do name=${i//[[:space:]]/}; name=${name%[.]*}; pdfimages -j -p "$i" $name; done
find . -name "*.ppm" -type f -size +20M -print0 | xargs -0 -r rm -rf
find . -name "*.ppm" -type f -size -130k -print0 | xargs -0 -r rm -rf
find . -name "*.pbm" -type f -print0 | xargs -0 -r rm -rf
mogrify -format jpg *.ppm
find . -name "*.ppm" -type f -print0 | xargs -0 -r rm -rf
find . -name "*.jpg" -type f -exec identify \{\} \; | awk '{split($3,a,"x"); if (a[1] < 30 && a[2] < 30) print $1}' | xargs -r rm -rf
find . -name "*.pdf" -type f -print0 | xargs -0 -r rm -rf