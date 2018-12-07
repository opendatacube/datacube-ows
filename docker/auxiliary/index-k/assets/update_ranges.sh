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

while getopts ":p:b:s:" o; do
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
    if [ -z "${suffixes[$i]}"  ] && [ -z "${first_suffix}" ]
    then
        suffix_string=""
    elif [ -z "${suffixes[$i]}" ]
    then
        suffix_string="${first_suffix}"
    else
        suffix_string="${suffixes[$i]}"
    fi
    s3-find "s3://${b}/${prefixes[$i]}" ${suffix_string:+"*$suffix_string"} | \
    s3-yaml-to-json | \
    dc-index-from-json
done

# update ranges in wms database

python3 /code/update_ranges.py --no-calculate-extent ${product:+"--product"} ${product:+"$product"}
