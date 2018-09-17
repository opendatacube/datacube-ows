#!/usr/bin/env bash
# Archive datasets in prefixes older than specified number of days
# Usage: -d days prior to current date to archive, optional, if not specified, will archive everything in prefix
#        -p prefix for search - only single prefix allowed
#        -b bucket containing data
#        -s suffix of metadata files, optional
#        -y UNSAFE if specified will do unsafe parsing of YAML files. Only use if targets are trusted

usage() { echo "Usage: $0 [-d <days>] -p <prefix> -b <bucket> [-s <suffix>] [-y UNSAFE]" 1>&2; exit 1; }

while getopts ":d:p:b:s:y:" o; do
    case "${o}" in
        d)
            days=${OPTARG}
            ;;
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
    esac
done
shift $((OPTIND-1))

if [ -z "${prefix}" ] || [ -z "${b}" ]; then
    usage
fi

if [ -n "${days}" ]
then
    # days is number of days older than current date
    # calculate date string
    todate=$(date -d"$(date) -${days} day" +%s) 
fi

# trim trailing '/' from prefix, we are adding it by default in search
p="${prefix%/}"

echo "$p"
# list of folders with names formated to be %Y-%m-%d
# grep for "PRE" to get folders
folders=$(aws s3 ls s3://${b}/${p}/ | grep "PRE " | awk '{print $2}' | sed 's/\/$//')
echo "$folders"
# archive data in folders older than todate
for folder in $folders; do
    if [ -n "${days}" ]
    then
        if [ $todate -gt $(date -d $folder +%s) ]; then
            python3 archiving/ls_s2_cog.py ${b} --prefix ${p}/$folder --archive ${suffix:+"--suffix"} ${suffix:+"$suffix"} ${safety:+"--unsafe"}
        fi
    else
        python3 archiving/ls_s2_cog.py ${b} --prefix ${p}/$folder --archive ${suffix:+"--suffix"} ${suffix:+"$suffix"} ${safety:+"--unsafe"}
    fi
done

python3 /code/update_ranges.py --no-calculate-extent
