for ignorefile in *-pyignore; do
    echo
    echo "##### $ignorefile #####"
    prefix=${ignorefile%-pyignore}
    cp $ignorefile root/.gitignore
    cd root
    #echo "## .gitignore:"
    cat .gitignore
    echo "## excluded:"
    ( find . | xargs git check-ignore -vn --no-index ) | grep -v "^::" |cut -f 2 | grep -v "./.gitignore" | tee ../${prefix}-excluded 
    echo "## included:"
    ( find . | xargs git check-ignore -vn --no-index ) | grep "^::" | cut -f 2 | grep -v "./.gitignore" | tee ../${prefix}-included
    echo "#####"
    cd -
done