#!/usr/bin/env python

from __future__ import division, print_function

import sys
import argparse
import re
from itertools import chain
from json import dump

from dark.titles import TitlesAlignments
from dark.fasta import FastaReads
from dark.fastq import FastqReads
from dark.utils import numericallySortFilenames


def readForTitle(titles, title):
    # Try the title and also the fields that result from splitting it
    # on its first space.
    for t in set([title] + title.split(maxsplit=1)):
        try:
            return titles.readsAlignments.getSubjectSequence(t)
        except KeyError:
            continue
    raise KeyError(title)


def writeJSON(titles, sampleName, verboseLabels):
    result = {
        'sampleName': sampleName,
        'x': [],
        'y': [],
        'matchingQueries': [],
        'text': [],
        'subjects': {},
        'queries': {},
    }

    for titleAlignments in titles.values():
        read = readForTitle(titles, titleAlignments.subjectTitle)
        title = read.id
        result['subjects'][title] = read.sequence

        for titleAlignment in titleAlignments:
            result['queries'][titleAlignment.read.id] = (
                titleAlignment.read.sequence)

        bestHsp = titleAlignments.bestHsp()
        matchLength = bestHsp.subjectEnd - bestHsp.subjectStart
        assert titleAlignments.subjectLength >= matchLength
        result['x'].append(matchLength)

        matchFraction = bestHsp.positiveCount / matchLength
        result['y'].append(matchFraction)

        matchingQueries = []
        matchingQueriesText = []
        for titleAlignment in titleAlignments:
            queryLength = len(titleAlignment.read)
            queryLengthAA = int(queryLength / 3)
            unmatchedAA = queryLengthAA - matchLength
            matchingQueries.append(titleAlignment.read.id)
            matchingQueriesText.append(
                '<strong>Matching query:</strong> %s (length %d nt / '
                '%d aa), %d aa (%.2f%%) unmatched' % (
                    titleAlignment.read.id,
                    queryLength,
                    queryLengthAA,
                    unmatchedAA,
                    unmatchedAA / queryLengthAA * 100))

        result['matchingQueries'].append(matchingQueries)

        if verboseLabels:
            text = (
                '<strong>Matched subject:</strong> %s<br>'
                '<strong>Subject length:</strong> %d aa<br>'
                '<strong>Matched region length:</strong> %d aa<br>'
                '<strong>Number of positive aa matches in region:</strong> %d '
                '(%.2f%%)<br>'
                '<strong>Subject coverage (across all matching queries):'
                '</strong> %.2f%%<br>'
                '<strong>Queries matching subject:</strong> %d<br>' % (
                    title,
                    titleAlignments.subjectLength,
                    matchLength,
                    bestHsp.positiveCount, matchFraction * 100,
                    titleAlignments.coverage() * 100,
                    titleAlignments.readCount()) +
                '<br>'.join(matchingQueriesText)
            )
        else:
            text = title

        result['text'].append(text)

    dump(result, sys.stdout, indent=2)


if __name__ == '__main__':

    # We do not use the addFASTACommandLineOptions and
    # parseFASTACommandLineOptions utility functions below because we allow
    # multiple FASTA or FASTQ files on the command line, which we specify
    # by --fasta and --fastq. And those names clash with the option names
    # used by those utility functions.

    parser = argparse.ArgumentParser(
        description=('Generate a plot of BLAST results showing the fraction '
                     'of positive amino acid matches (in the matched region) '
                     'against the matched region length'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--earlyExit', default=False, action='store_true',
        help=('If True, just print the number of interesting matches, but do '
              'not create the plot. Implies --printHits.'))

    parser.add_argument(
        '--verboseLabels', default=False, action='store_true',
        help=('If True, show additional match information in the hover-over '
              'popup for plot labels.'))

    parser.add_argument(
        '--printHits', default=False, action='store_true',
        help=('If True, print a listing of all the BLAST hits. '
              'The columns in the output are '
              '1) coverage fraction, '
              '2) median bit score of matching query, '
              '3) best bit score of matching queries, '
              '4) number of matching queries, '
              '5) total hsp count for the subject'
              '6) subject length'
              '7) subject title.'))

    parser.add_argument(
        '--matcher', default='blast', choices=('blast', 'diamond'),
        help='The matching algorithm that was used to produce the JSON.')

    parser.add_argument(
        '--json', metavar='JSON-file', nargs='+', action='append',
        required=True, help='the JSON file(s) of BLAST or DIAMOND output.')

    # A mutually exclusive group for either FASTA or FASTQ files.
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--fasta', metavar='FASTA-file', nargs='+', action='append',
        help=('the FASTA file(s) of sequences that were given to BLAST '
              'or DIAMOND.'))

    group.add_argument(
        '--fastq', metavar='FASTQ-file', nargs='+', action='append',
        help=('the FASTQ file(s) of sequences that were given to BLAST '
              'or DIAMOND.'))

    parser.add_argument(
        '--databaseFastaFilename',
        help=('The filename of the FASTA file used to make the BLAST or '
              'DIAMOND database. If --matcher diamond is used, either this '
              'argument or --sqliteDatabaseFilename must be specified. If '
              '--matcher blast is used these options can be omitted, in '
              'which case the code will fall back to using blastdbcmd, '
              'which can be unreliable. See also --sqliteDatabaseFilename '
              'for a way to enable fast subject lookup for either matcher.'))

    parser.add_argument(
        '--sqliteDatabaseFilename',
        help=('The filename of the sqlite3 database file of FASTA metadata, '
              'made from the FASTA that was used to make the BLAST or DIAMOND '
              'database. If --matcher diamond is used, either this argument '
              'or --databaseFilename must be specified.'))

    parser.add_argument(
        '--databaseFastaDirectory',
        help=('The directory where the FASTA file used to make the BLAST or '
              'DIAMOND database can be found. This argument is only useful '
              'when --sqliteDatabaseFilename is specified.'))

    # Args for filtering on ReadsAlignments.
    parser.add_argument(
        '--minStart', type=int, default=None,
        help='Reads that start before this subject offset should not be '
        'shown.')

    parser.add_argument(
        '--maxStop', type=int, default=None,
        help='Reads that end after this subject offset should not be shown.')

    parser.add_argument(
        '--oneAlignmentPerRead', default=False, action='store_true',
        help='If True, only keep the best alignment for each read.')

    parser.add_argument(
        '--maxAlignmentsPerRead', type=int, default=None,
        help=('Reads with more than this many alignments will be elided. Pass '
              'zero to only keep reads with no matches (alignments).'))

    parser.add_argument(
        '--scoreCutoff', type=float, default=None,
        help=('A float score. Matches with scores worse than this will be '
              'ignored.'))

    parser.add_argument(
        '--maxHspsPerHit', type=int, default=None,
        help='A numeric max number of HSPs to show for each hit on hitId.')

    parser.add_argument(
        '--whitelist', nargs='+', default=None, action='append',
        help='sequence titles that should be whitelisted')

    parser.add_argument(
        '--blacklist', nargs='+', default=None, action='append',
        help='sequence titles that should be blacklisted')

    parser.add_argument(
        '--titleRegex', default=None,
        help='a regex that sequence titles must match.')

    parser.add_argument(
        '--negativeTitleRegex', default=None,
        help='a regex that sequence titles must not match.')

    parser.add_argument(
        '--truncateTitlesAfter', default=None,
        help=('a string that titles will be truncated beyond. If the '
              'truncated version of a title has already been seen, '
              'that title will be skipped.'))

    parser.add_argument(
        '--minSequenceLen', type=int, default=None,
        help='sequences of lesser length will be elided.')

    parser.add_argument(
        '--maxSequenceLen', type=int, default=None,
        help='sequences of greater length will be elided.')

    parser.add_argument(
        '--taxonomy', default=None,
        help=('a string of the taxonomic group on which should be '
              'filtered. eg "Vira" will filter on viruses.'))

    # Args for filtering on TitlesAlignments.
    parser.add_argument(
        '--minMatchingReads', type=int, default=None,
        help='sequences that are matched by fewer reads will be elided.')

    parser.add_argument(
        '--minMedianScore', type=float, default=None,
        help=('sequences that are matched with a median score that is '
              'worse will be elided.'))

    parser.add_argument(
        '--withScoreBetterThan', type=float, default=None,
        help=('sequences that are matched without at least one score '
              'at least this good will be elided.'))

    parser.add_argument(
        '--minNewReads', type=float, default=None,
        help=('The fraction of its reads by which a new read set must differ '
              'from all previously seen read sets in order to be considered '
              'acceptably different.'))

    parser.add_argument(
        '--maxTitles', type=int, default=None,
        help=('The maximum number of titles to keep. If more titles than '
              'this result from the filtering, titles will be sorted '
              '(according to the --sortOn value) and only the best will be '
              'retained.'))

    parser.add_argument(
        '--minCoverage', type=float, default=None,
        help=('The (0.0 to 1.0) minimum fraction of a subject sequence that '
              'must be matched by at least one read.'))

    parser.add_argument(
        '--sortOn', default='maxScore',
        choices=('maxScore', 'medianScore', 'readCount', 'length', 'title'),
        help='The attribute to sort subplots on.')

    parser.add_argument(
        '--sortFilenames', default=False, action='store_true',
        help=('If specified, the JSON and FASTA/Q file names will be '
              'processed in sorted order. The sorting is based on finding '
              'a numerical prefix in the filename. This can be useful when '
              'processing output files produced by systems like HTCondor, '
              'which makes files with names like 1.out, 10.out, etc. that do '
              'not sort properly and so cannot conveniently be given to this '
              'program along with a single FASTA/Q file (because the order of '
              'the results in the files from HTCondor does not match the '
              'order of sequences in the FASTA/Q file.'))

    args = parser.parse_args()

    if args.earlyExit:
        # Make sure we do something useful if we're exiting early.
        args.printHits = True

    # Flatten lists of lists that we get from using both nargs='+' and
    # action='append'. We use both because it allows people to use (e.g.)
    # --json on the command line either via "--json file1 --json file2" or
    # "--json file1 file2", or a combination of these. That way it's not
    # necessary to remember which way you're supposed to use it and you also
    # can't be hit by the subtle problem encountered in
    # https://github.com/acorg/dark-matter/issues/453
    jsonFiles = list(chain.from_iterable(args.json))
    whitelist = (
        set(chain.from_iterable(args.whitelist)) if args.whitelist else None)
    blacklist = (
        set(chain.from_iterable(args.blacklist)) if args.blacklist else None)

    if args.fasta:
        if args.sortFilenames:
            files = numericallySortFilenames(chain.from_iterable(args.fasta))
        else:
            files = list(chain.from_iterable(args.fasta))
        reads = FastaReads(files)
    else:
        if args.sortFilenames:
            files = numericallySortFilenames(chain.from_iterable(args.fastq))
        else:
            files = list(chain.from_iterable(args.fastq))
        reads = FastqReads(files)

    if args.matcher == 'blast':
        from dark.blast.alignments import BlastReadsAlignments
        readsAlignments = BlastReadsAlignments(
            reads, jsonFiles, databaseFilename=args.databaseFastaFilename,
            databaseDirectory=args.databaseFastaDirectory,
            sqliteDatabaseFilename=args.sqliteDatabaseFilename,
            sortBlastFilenames=args.sortFilenames)
    else:
        # Must be 'diamond' (due to parser.add_argument 'choices' argument).
        if (args.databaseFastaFilename is None and
                args.sqliteDatabaseFilename is None):
            print('Either --databaseFastaFilename or --sqliteDatabaseFilename '
                  'must be used with --matcher diamond.', file=sys.stderr)
            sys.exit(1)
        elif not (args.databaseFastaFilename is None or
                  args.sqliteDatabaseFilename is None):
            print('--databaseFastaFilename and --sqliteDatabaseFilename '
                  'cannot both be used with --matcher diamond.',
                  file=sys.stderr)
            sys.exit(1)

        from dark.diamond.alignments import DiamondReadsAlignments
        readsAlignments = DiamondReadsAlignments(
            reads, jsonFiles, sortFilenames=args.sortFilenames,
            databaseFilename=args.databaseFastaFilename,
            databaseDirectory=args.databaseFastaDirectory,
            sqliteDatabaseFilename=args.sqliteDatabaseFilename)

    sampleName = re.search('\d+-\d+', files[0]).group(0)

    if sampleName is None:
        print('Input file name %r did not match the sample name regex' %
              files[0], file=sys.stderr)
        sys.exit(1)

    readsAlignments.filter(
        maxAlignmentsPerRead=args.maxAlignmentsPerRead,
        minSequenceLen=args.minSequenceLen,
        maxSequenceLen=args.maxSequenceLen,
        minStart=args.minStart, maxStop=args.maxStop,
        oneAlignmentPerRead=args.oneAlignmentPerRead,
        maxHspsPerHit=args.maxHspsPerHit,
        scoreCutoff=args.scoreCutoff,
        whitelist=whitelist, blacklist=blacklist,
        titleRegex=args.titleRegex, negativeTitleRegex=args.negativeTitleRegex,
        truncateTitlesAfter=args.truncateTitlesAfter, taxonomy=args.taxonomy)

    titlesAlignments = TitlesAlignments(readsAlignments).filter(
        minMatchingReads=args.minMatchingReads,
        minMedianScore=args.minMedianScore,
        withScoreBetterThan=args.withScoreBetterThan,
        minNewReads=args.minNewReads, maxTitles=args.maxTitles,
        sortOn=args.sortOn, minCoverage=args.minCoverage)

    nTitles = len(titlesAlignments)

    if args.printHits and nTitles:
        print('Found %d interesting title%s.' %
              (nTitles, '' if nTitles == 1 else 's'), file=sys.stderr)
        print(titlesAlignments.tabSeparatedSummary(sortOn=args.sortOn),
              file=sys.stderr)

    if args.earlyExit:
        sys.exit(0)

    if nTitles == 0:
        print('No output generated due to no matching titles.',
              file=sys.stderr)
        sys.exit(0)

    writeJSON(titlesAlignments, sampleName, args.verboseLabels)
