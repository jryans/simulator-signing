#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import glob

VERSIONS = ["1.3", "1.4", "2.0", "2.1", "2.2", "3.0"]
PLATFORMS = ["mac64", "win32", "linux64", "linux"]
SIMULATOR_DIR = "/pub/mozilla.org/labs/fxos-simulator/#VERSION#/#OS#/"
LATEST_NAME = "fxos_#SLASHED_VERSION#_simulator-#OS#-latest.xpi"
SIMULATOR_LINK = "https://ftp.mozilla.org/pub/mozilla.org/labs/fxos-simulator/#VERSION#/#OS#/fxos_#SLASHED_VERSION#_simulator-#OS#-latest.xpi"
VERSION_SUFFIX = ".1-signed"

def process(version, slashed_version, platform):
    file_name = "fxos_%s_simulator-*-%s.xpi" % (slashed_version, platform)
    print("Processing %s" % file_name)
    if not glob.glob(file_name):
        print("Downloading %s" % file_name)
        subprocess.call(["scp", "people.mozilla.org:~/simulators-signed/%s" % file_name, "."])
    file_name = glob.glob(file_name)[0]
    print("Deploying %s" % file_name)
    os.chmod(file_name, 0o664)
    remote_dir = re.sub(r"\#OS\#", platform, SIMULATOR_DIR)
    remote_dir = re.sub(r"\#VERSION\#", version, remote_dir)
    subprocess.call(["scp", "-p", file_name, "stage.mozilla.org:%s" % remote_dir])
    latest_name = re.sub(r"\#OS\#", platform, LATEST_NAME)
    latest_name = re.sub(r"\#SLASHED_VERSION\#", slashed_version, latest_name)
    print("Updating symlink %s" % latest_name)
    subprocess.call("ssh stage.mozilla.org 'cd %s && ln -snf %s %s'" % (remote_dir, file_name, latest_name), shell = True)
    print("Updating update.rdf")
    new_version = re.search(r"-(.*)-%s" % platform, file_name).group(1)
    update_link = "https://ftp.mozilla.org%s%s" % (remote_dir, file_name)
    update_link = update_link.replace("/", "\\/")
    subprocess.call("ssh stage.mozilla.org \"cd %s && sed -i 's/<em:version>.*<\/em:version>/<em:version>%s<\/em:version>/;s/<em:updateLink>.*<\/em:updateLink>/<em:updateLink>%s<\/em:updateLink>/' update.rdf\"" % (remote_dir, new_version, update_link), shell = True)

for version in VERSIONS:
    for platform in PLATFORMS:
        slashed_version = re.sub(r"\.", "_", version)
        process(version, slashed_version, platform)
