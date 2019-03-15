#!/bin/bash
# Index new datasets and update ranges for WMS
# should be run after archiving old datasets so that
# ranges for WMS are correct
# environment variables:
# Usage: -p prefix(es) for search. If multiple use space seperated list enclosed in quotes
#        -b bucket containing data
#        -s suffix for search (optional). If multiple use space separated list enclosed in quotes
#                                         If multiple must be same length as prefix list,
#                                         if only one provided, suffix will be applied to ALL prefixes
#        -y UNSAFE: If set script will use unsafe YAML reading. Only set if you fully trust source
#        -d product to update in database (optional)
# e.g. ./update_ranges -b dea-public-data -p "L2/sentinel-2-nrt/S2MSIARD/2018 L2/sentinel-2-nrt/2017"

usage() { echo "Usage: $0 -p <prefix> -b <bucket> [-s <suffix>] [-y UNSAFE]" 1>&2; exit 1; }

while getopts ":p:b:s:y:d:" o; do
    case "${o}" in
        p)
            prefix=${OPTARG}
            ;;
        b)
            b=${OPTARG}
            ;;
        s)
            suffix=${OPTARG}
            ;;
        y)
            safety=${OPTARG}
            ;;
        d)
            product=${OPTARG}
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${prefix}" ] || [ -z "${b}" ]; then
    usage
fi

IFS=' ' read -r -a prefixes <<< "$prefix"
IFS=' ' read -r -a suffixes <<< "$suffix"
IFS=' ' read -r -a products <<< "$product"
first_suffix="${suffixes[0]}"
safety_arg=""

if [ "$safety" == "UNSAFE" ]
then
    safety_arg="--unsafe"
fi

# index new datasets
# prepare script will add new records to the database
for i in "${!prefixes[@]}"
do
    s3-find "s3://${b}/${prefixes[$i]}" | \
    s3-to-tar | \
    dc-index-from-tar
done

# update ranges in wms database

if [ -z "$product" ]
then
    python3 /code/update_ranges.py --no-calculate-extent
else

    for i in "${!products[@]}"
    do
        python3 /code/update_ranges.py --no-calculate-extent --product "${products[$i]}"
    done
fi

#python3 /code/update_ranges.py --no-calculate-extent ${product:+"--product"} ${product:+"$product"}
