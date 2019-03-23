#!/bin/bash

set -eu
set -o pipefail

# You'll want to replace this IP address with your Package Drone's instance's URL.
readonly PACKAGE_DRONE_URL=192.168.1.101:8083
readonly P2_MIRROR_NAME=P2Mirror

# bash doesn't support two-dimensional arrays, we'll just have to iterate through two array and be sure to keep them matched up.
declare -a readonly IDS=(
    R20140525021250
    paho
)

declare -a readonly REPO_URLS=(
    http://download.eclipse.org/tools/orbit/downloads/drops/R20140525021250/repository
    http://download.eclipse.org/paho/
)

print_usage() {
cat << EOF
Usage: ${0##*/} --username DEPLOY_USERNAME --password DEPLOY_PASSWORD

Options:
    --username  [DEPLOY_USERNAME]  The deploy username, this needs to match up with the username of a key that is
                                        allowed to upload to the Package Drone Channel.
    --password  [DEPLOY_PASSWORD]  The deploy password, this needs to match up with the password of a key that is
                                        allowed to upload to the Package Drone Channel.
    -h|--help   display this help and exit.
EOF
}

DEPLOY_USERNAME=
DEPLOY_PASSWORD=

main() {

    # parse parameters
    while [[ $# -ge 1 ]]
    do
        key="$1"
        case $key in

            --username)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    print_usage
                    exit 1
                fi
                DEPLOY_USERNAME="$2"
                shift
                ;;
            --password)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    print_usage
                    exit 1
                fi
                DEPLOY_PASSWORD="$2"
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                echo "Unknown parameter '$key'. Type $0 -h for more information."
                exit 1
                ;;
        esac
        shift
    done

    if [ -z "$DEPLOY_USERNAME" ]; then
        print_usage
        exit 1
    fi

    if [ -z "$DEPLOY_PASSWORD" ]; then
        print_usage
        exit 1
    fi

    for i in "${!IDS[@]}"; do
        generate_compressed_copy_of_p2_repo ${IDS[i]} ${REPO_URLS[i]}
    done



}

# Generate compressed copy of remote p2 repo and upload it to package drone
# $1 The repo ID, a unique string that will set the final name of the zip file uploaded to package drone
# $2 The URL of the remote P2 repo
generate_compressed_copy_of_p2_repo() {
    # Download the metadata (content.jar)
    /opt/eclipse/eclipse -nosplash -verbose -application org.eclipse.equinox.p2.metadata.repository.mirrorApplication -source "$2" -destination ./repo

    # Download the artifacts
    /opt/eclipse/eclipse -nosplash -verbose -application org.eclipse.equinox.p2.artifact.repository.mirrorApplication -source "$2" -destination ./repo

    (cd ./repo && zip -r ../repo.zip ./*) && rm -r ./repo

    upload_binary_to_package_drone "$1"
    rm ./repo.zip
}

# Upload file to package-drone
# $1 - file name in repo (not on local filesystem)
# $2 - channel naem or ID to upload to
upload_binary_to_package_drone() {
    EPOCH=$(date +%s)
    curl -X PUT --data-binary @repo.zip "http://$DEPLOY_USERNAME:$DEPLOY_PASSWORD@$PACKAGE_DRONE_URL/api/v3/upload/plain/channel/$P2_MIRROR_NAME/$1.zip?filesystem:name=$1&filesystem:epoch=$EPOCH"
}

main "$@"
