#!/bin/bash
# Purpose: release script for braiins OS firmware

# The script:
# - runs a build of braiins-os for all specified targets
# - and generates scripts for packaging and signing the resulting build of
#
#
# Synopsis: ./build-release.sh KEYRINGSECRET RELEASE PACKAGEMERGE SUBTARGET1 [SUBTARGET2 [SUBTARGET3...]]
set -e
#
parallel_jobs=32
# default target is zynq
target=zynq
git_repo=git@gitlab.bo:x/braiins-os
feeds_url=https://feeds.braiins-os.org
pool_user=!non-existent-user!
fw_prefix=braiins-os
output_dir=output

key=`realpath $1`
shift
date_and_patch_level=$1
shift
package_merge=$1
shift
release_subtargets=$@

#DRY_RUN=echo
STAGE1=y
CLONE=n

echo ID is: `id`
echo KEY is: $key
echo RELEASE_BUILD_DIR is: $RELEASE_BUILD_DIR
echo DATE and PATCH LEVEL: $date_and_patch_level
echo RELEASE SUBTARGETS: $release_subtargets

if [ $CLONE = y ]; then
    $DRY_RUN mkdir -p $RELEASE_BUILD_DIR
    $DRY_RUN cd $RELEASE_BUILD_DIR
    $DRY_RUN git clone $git_repo
    # Prepare build environment
    $DRY_RUN cd braiins-os
fi

. prepare-env.sh

function generate_sd_img() {
    src_dir=$1
    sd_img=$2
    echo dd if=/dev/zero of=$sd_img bs=1M count=32
    echo parted $sd_img --script mktable msdos
    echo parted $sd_img --script mkpart primary fat32 2048s 16M
    echo parted $sd_img --script mkpart primary ext4 16M 32M

    echo sudo kpartx -s -av $sd_img
    echo sudo mkfs.vfat /dev/mapper/loop0p1
    echo sudo mkfs.ext4 /dev/mapper/loop0p2
    echo sudo mount /dev/mapper/loop0p1 /mnt
    echo sudo cp $src_dir/'sd/*' /mnt/
    echo sudo umount /mnt
    echo sudo kpartx -d $sd_img
}

if [ "$date_and_patch_level" != "current" ]; then
	tag=`git tag | grep $date_and_patch_level | tail -1`
	if [ -z "$tag" ]; then
		echo "Error: supplied release \"$date_and_patch_level\" not found in tags"
		exit 4
	else
		$DRY_RUN git checkout $tag
	fi
fi

# get build version for current branch
version=$(./bb.py build-version)

# Iterate all releases/switch repo and build
for subtarget in $release_subtargets; do
    # latest release
    platform=$target-$subtarget
    # We need to ensure that feeds are update
    if [ $STAGE1 = y ]; then
	$DRY_RUN ./bb.py --platform $platform prepare
	$DRY_RUN ./bb.py --platform $platform prepare --update-feeds
	# build everything for a particular platform
	$DRY_RUN ./bb.py --platform $platform build --key $key -j$parallel_jobs -v
    fi

    package_name=${fw_prefix}_${subtarget}_${version}
    platform_dir=$output_dir/$package_name

    # Deploy SD and upgrade images
    for i in sd upgrade; do
	$DRY_RUN ./bb.py --platform $platform deploy local_$i:$platform_dir/$i --pool-user $pool_user
    done

    # Feeds deploy is specially handled as it has to merge with firmware packages
    packages_url=$feeds_url/$subtarget/Packages

    if [ "$package_merge" == "true" ]; then
	echo Merging package list with previous release for $platform...
	extra_feeds_opts="--feeds-base $packages_url"
    else
	echo Nothing has been published for $platform, skipping merge of Packages...
	extra_feeds_opts=
    fi
    $DRY_RUN ./bb.py --platform $platform deploy local_feeds:$platform_dir/feeds $extra_feeds_opts --pool-user $pool_user

    # Generate script for publication
    ($DRY_RUN cd $output_dir;
     pack_and_sign_script=pack-and-sign-$package_name.sh
     publish_dir=./publish/$package_name
     sd_img=$publish_dir/${fw_prefix}_${subtarget}_sd_${version}.img
     gpg_opts="--armor --detach-sign --sign-with release@braiins.cz --sign"
     echo set -e > $pack_and_sign_script
     echo mkdir -p $publish_dir >> $pack_and_sign_script
     echo cp -r $package_name/feeds/ $publish_dir >> $pack_and_sign_script
     generate_sd_img $package_name $sd_img >> $pack_and_sign_script
     echo gpg2 $gpg_opts $sd_img >> $pack_and_sign_script
     echo for upgrade_img in $package_name/upgrade/\*\; do >> $pack_and_sign_script
     echo cp \$upgrade_img $publish_dir >> $pack_and_sign_script
     echo gpg2 $gpg_opts $publish_dir/\$\(basename \$upgrade_img\) >> $pack_and_sign_script
     echo
     echo done >> $pack_and_sign_script
    )
done
