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
import errno
import shutil
import subprocess

def image_index(img_key):
    return {
        'englishCA' : 'enCAimg',
        'englishSA' : 'enSAimg',
        'spanishCA' : 'esCAimg',
        'spanishSA' : 'esSAimg',
        }[img_key]

def get_current_week():
    return "week" + str(datetime.date.isocalendar(datetime.date.today())[1])

def get_user_image_path(img):
    return os.path.join(os.environ['HOME'], 'slides', img + '.png')

def create_fehbg_file(img_path):
    # create the ~/.fehbg file for the user this script is run as
    feh_cmd = 'feh --bg-fill' + ' "' + get_user_image_path(img_path) + '"\n'
    try: 
        with open(os.path.expanduser('~/.fehbg'),'w') as f:
            f.write(feh_cmd)
            f.close()
    except IOError as e:
        logging.CRITICAL("ERROR: unable to write fehbg file with command: %s" % feh_cmd)
        logging.debug("Error message was: %s" % e)

def create_local_dir(dir):
    # ensure local directory exists
    try:
        os.mkdir(os.path.join(os.environ['HOME'], dir))
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            logging.debug("An issue was encountered creating the local directory")
            raise

def ensure_mount_point_exists(mountpoint):
    mount_args = ["mount", mountpoint]
    try:
        os.mkdir(mountpoint)
        if subprocess.call(mount_args) != 0:
            logging.debug("unable to ensure mounted filesystem: %s" % mountpoint)
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            logging.debug("An issue was encountered creating with the network share")
            logging.debug("Error was: %s" % err)
            raise

def copy_images_from_share(src, dst):
    # refresh all images from image share (delete and recopy)
    try:
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    except OSError as err:
        logging.CRITICAL("An error occured: %s" % err)

def main():
    # arguments are fun!
    parser = argparse.ArgumentParser(description='Utility script to parse SAD/CA schedule file and update theme images')
    parser.add_argument('--debug', dest='verbose', action='store_const', const=1, help='Enable debug logging')
    parser.add_argument('--filename', dest='filename', action='store', default='schedule.txt', help='Filename of schedule file')
    parser.add_argument('--logfile', dest='logfile', default=False, help='Log to a file instead of stdout')
    args = parser.parse_args()

    # handle some args
    # this is ugly
    if args.logfile and args.verbose:
        logging.basicConfig(filename=args.logfile, level=logging.DEBUG)
    elif args.logfile:
        logging.basicConfig(filename=args.logfile, level=logging.INFO)
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    logging.debug("All args: %s" % args)
    # process
    try:
        process_dir = os.path.expanduser('~/slides/')
        with open(os.path.join(process_dir, args.filename), 'r') as f:
            for line in f:
                config = line.rstrip().split('=')
                if config[0] == get_current_week():
                    # determine value in config[]
                    logging.debug("current week found in file as:  %s" % config[0])
                    logging.debug("image key name: %s" % config[1])
                    # and set file accordingly
                    # link_file() or create_dot_fehbg_file()
                    logging.debug("image file name: %s" % image_index(config[1]))
                    create_local_dir('slides')
                    create_fehbg_file(image_index(config[1]))
                    ensure_mount_point_exists("/mnt/wahdocs")
                    copy_images_from_share("/mnt/wahdocs/slides", # FIX
                                           os.path.expanduser("~/slides"))
    except IOError as e:
        logging.CRITICAL("ERROR: schedule file not found: %s, %s" % args.filename, e)

if __name__ == '__main__':
    main()
