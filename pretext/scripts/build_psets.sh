#!/bin/zsh

# 05-01 05-05 06-01 06-02a 06-02b
for pset in $@
    do for fmt in tex pdf scorm
        do pretext build $pset-$fmt
        pretext build $pset-$fmt-sols
    done
done