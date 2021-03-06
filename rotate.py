#!/usr/bin/env python
#########
# Purpose: Automatically rotate image files based on the plain text
#   schedule of weeks. SAD and CA theme text will be autodisplayed as
#   the only window use the `feh` image viewer
#
# Intended Audience: Sysadmin, Basic familiarity with python is helpful, but
#   this script should be easily understood (and does not exemplify
#   good python practices.)
#
# Usage: Run this script on a scheduled basis (via cron) and then add the
#   following to the startup script:"eval $(cat ~/.fehbg)"
#
# Depends:
#   feh `apt-get -q -y install feh`
#   correct mount point settings in /etc/fstab to allow user mounts (-o users)
#
#########

import argparse
import datetime
import logging
import os
import shutil
import subprocess


def get_current_week():
    return "week" + str(datetime.date.isocalendar(datetime.date.today())[1])


def get_todays_date():
    # return date as 8 digit, yr first: 20121023
    return str(datetime.date.isoformat(datetime.date.today())).replace('-','')


def get_user_image_path(img):
    return os.path.join(os.environ['HOME'], 'slides', img + '.jpg')


def create_fehbg_file(img):
    # create the ~/.fehbg file for the user this script is run as
    feh_cmd = 'feh --bg-fill' + ' "' + get_user_image_path(img) + '"\n'
    try:
        with open(os.path.expanduser('~/.fehbg'), 'w') as f:
            f.write(feh_cmd)
    except IOError as e:
        logging.exception("ERROR: unable to write fehbg file with command: %s",
                          feh_cmd)
        logging.debug("Error message was: %s", e)


def create_local_dir(dir):
    # ensure local directory exists
    local_dir = os.path.join(os.environ['HOME'], dir)
    if os.path.exists(local_dir):
        logging.warning("Directory already exists")
        return
    else:
        os.makedirs(local_dir)
        logging.debug("Directory created: %s", local_dir)


def ensure_mount_point_exists(mountpoint):
    mount_args = ["mount", mountpoint]
    if os.path.exists(mountpoint):
        logging.debug("Mount point already exists: %s Doing nothing",
                        mountpoint)
        return
    else:
        os.makedirs(mountpoint)
        subprocess.call(mount_args) != 0


def refresh_images_from_share(src, dst):
    # refresh all images from image share (delete and recopy)
    try:
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    except OSError as e:
        logging.critical("An error occured: %s", e)


def main():
    # arguments are fun!
    parser = argparse.ArgumentParser(description='Utility script to parse SAD/CA schedule file and update theme images')
    parser.add_argument('--debug', dest='verbose', action='store_true', default=False, help='Enable debug logging (default: off)')
    parser.add_argument('--filename', dest='filename', action='store', default='schedule.txt', help='Filename of schedule file (default: schedule.txt)')
    parser.add_argument('--logfile', dest='logfile', default=None, help='Log to a file instead of stdout (default: None)')
    args = parser.parse_args()

    # handle some args
    # this is ugly
    if args.logfile and args.verbose:
        logging.basicConfig(filename=args.logfile, level=logging.DEBUG)
    elif args.logfile:
        logging.basicConfig(filename=args.logfile, level=logging.CRITICAL)
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug("All args: %s", args)
    # process
    process_dir = os.path.expanduser('~/slides/')
    if os.path.exists(process_dir):
        logging.debug("Directory already exists")
    else:
        os.makedirs(process_dir)
        logging.debug("Directory created: %s", process_dir)

    ensure_mount_point_exists("/mnt/wahdocs")
    refresh_images_from_share("/mnt/wahdocs/slides", process_dir)

    try:
        with open(os.path.join(process_dir, args.filename), 'r') as f:
            for line in f:
                config = line.rstrip().split('=')
                logging.debug("date found in file as:  %s", config[0])
                logging.debug("image file name: %s", config[1])
                logging.debug("Current date is: %s", get_todays_date())
                if config[0] == get_todays_date():
                    create_fehbg_file(config[1])
    except IOError as e:
        logging.exception("ERROR: schedule file not found: %s, %s", args.filename, e)

if __name__ == '__main__':
    main()
