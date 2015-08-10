#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import fileinput

VERSIONS = ["1.3", "1.4", "2.0", "2.1", "2.2", "3.0"]
PLATFORMS = ["mac64", "win32", "linux64", "linux"]
SIMULATOR_LINK = "https://ftp.mozilla.org/pub/mozilla.org/labs/fxos-simulator/#VERSION#/#OS#/fxos_#SLASHED_VERSION#_simulator-#OS#-latest.xpi"
SIMULATOR_PATH = "/pub/mozilla.org/labs/fxos-simulator/#VERSION#/#OS#/fxos_#SLASHED_VERSION#_simulator-#OS#-latest.xpi"
VERSION_SUFFIX = ".1-signed"

def process(remote_path, slashed_version, platform):
    file_name = os.path.basename(remote_path)
    print("Processing %s" % file_name)
    if not os.path.exists(file_name):
        print("Downloading %s" % remote_path)
        subprocess.call(["scp", "stage.mozilla.org:%s" % remote_path, "."])
    dir_name = os.path.splitext(file_name)[0]
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    print("Expanding %s" % file_name)
    os.mkdir(dir_name)
    subprocess.call(["unzip", "-d", dir_name, file_name])
    new_version = VERSION_SUFFIX
    with fileinput.input(os.path.join(dir_name, "install.rdf"), inplace = True) as rdf:
        for line in rdf:
            match = re.search(r"<em:version>(.+)</em:version>", line)
            if match:
                new_version = match.group(1) + new_version
                print(re.sub(r"<em:version>(.+)</em:version>", r"<em:version>\1.1-signed</em:version>", line), end = "")
            else:
                print(line, end = "")
    upd_file_name = "fxos_%s_simulator-%s-%s.xpi" % (slashed_version, new_version, platform)
    print("Creating %s" % upd_file_name)
    subprocess.call(["zip", "-r", "../%s" % upd_file_name, "."], cwd = dir_name)
    os.chmod(upd_file_name, 0o666)
    print("Uploading %s" % upd_file_name)
    subprocess.call(["scp", "-p", upd_file_name, "people.mozilla.org:~/simulators/"])

for version in VERSIONS:
    for platform in PLATFORMS:
        slashed_version = re.sub(r"\.", "_", version)
        link = re.sub(r"\#OS\#", platform, SIMULATOR_PATH)
        link = re.sub(r"\#VERSION\#", version, link)
        link = re.sub(r"\#SLASHED_VERSION\#", slashed_version, link)
        process(link, slashed_version, platform)
        break
    break
