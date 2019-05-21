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
#        -y skip check for full depth to scan the path in S3
#        -d product to update in database (optional)
#        -l Set if to ignore lineage
#        -e exclude product to index
#        -m multi-product update ranges
#
# e.g. ./update_ranges -b dea-public-data -p "L2/sentinel-2-nrt/S2MSIARD/2018 L2/sentinel-2-nrt/2017"

usage() { echo "Usage: $0 -p <prefix> -b <bucket> [-s <suffix>] [-y UNSAFE]" 1>&2; exit 1; }

while getopts ":p:b:s:y:d:m:l:e:" o; do
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
        m)
            multiproduct=${OPTARG}
            ;;
        l)
            lineage=${OPTARG}
            ;;
        e)
            exclude=${OPTARG}
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
IFS=' ' read -r -a multiproducts <<< "$multiproduct"
first_suffix="${suffixes[0]}"
safety_arg=""


if [ "$safety" == "SAFE" ]
then
    safety_arg="--skip-check"
fi

# index new datasets
# prepare script will add new records to the database
for i in "${!prefixes[@]}"
do
    if [ -n "$lineage" ] && [ -n "$exclude" ]
    then
        s3-find $safety_arg "s3://${b}/${prefixes[$i]}" | \
        s3-to-tar | \
        dc-index-from-tar --exclude-product $exclude --ignore-lineage
    elif [ -n "$exclude" ]
    then
        s3-find $safety_arg "s3://${b}/${prefixes[$i]}" | \
        s3-to-tar | \
        dc-index-from-tar --exclude-product $exclude
    elif [ -n "$lineage" ]
    then
        s3-find $safety_arg "s3://${b}/${prefixes[$i]}" | \
        s3-to-tar | \
        dc-index-from-tar --ignore-lineage
    else
        s3-find $safety_arg "s3://${b}/${prefixes[$i]}" | \
        s3-to-tar | \
        dc-index-from-tar
    fi
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
if [ -n "$multiproduct" ]
then
    for i in "${!multiproducts[@]}"
    do
        python3 /code/update_ranges.py --no-calculate-extent --multiproduct "${multiproducts[$i]}"
    done
fi

#python3 /code/update_ranges.py --no-calculate-extent ${product:+"--product"} ${product:+"$product"}
