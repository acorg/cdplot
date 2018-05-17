#!/bin/bash -e

tmp=/tmp/$0-$$.json
trap "rm -f $tmp" 0 1 2 3 15

dbFasta=RVDB-prot-1KV-ECH-no-id-dups.fasta

test -f $dbFasta || {
    echo "Database FASTA file '$dbFasta' does not exist." >&2
    exit 1
}

sqliteDb=RVDB-prot-1KV-ECH-no-id-dups.db

test -f $sqliteDb || {
    make-fasta-database.py --out $sqliteDb --fasta $dbFasta
}


for sample in "$@"
do
    xml=$sample-blastx-RVDB.xml

    test -f $xml || {
        echo "BLAST XML file '$xml' does not exist." >&2
        exit 1
    }

    contigs=$sample-contigs.fasta

    test -f $contigs || {
        echo "FASTA contigs file '$contigs' does not exist." >&2
        exit 1
    }

    convert-blast-xml-to-json.py --xml $xml > $tmp
    dm-json-to-json.py --fasta $contigs --json $tmp --verboseLabels \
                       --sqliteDatabaseFilename $sqliteDb > $sample.json
    rm -f $tmp
done
