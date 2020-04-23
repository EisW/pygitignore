for ignorefile in *-pyignore; do
    echo
    echo "##### $ignorefile #####"
    prefix=${ignorefile%-pyignore}
    cp $ignorefile root/.gitignore
    cd root
    #echo "## .gitignore:"
    cat .gitignore
    echo "## excluded:"
    ( find . -type f | xargs git check-ignore --no-index ) | grep -v "./.gitignore" | tee ../${prefix}-excluded 
    echo "## included:"
    for f in $(find . -type f | grep -v "./.gitignore"); do
        excluded=0
        while read line; do if [ "$line" == "$f" ]; then excluded=1; fi; done < ../${prefix}-excluded
        if [ $excluded -eq 0 ]; then
            echo $f
        fi
    done | tee ../${prefix}-included
    echo "#####"
    cd -
    rm root/.gitignore
done