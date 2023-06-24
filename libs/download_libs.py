import json
import sys
import urllib.request as req
from pathlib import Path
from urllib.error import HTTPError, URLError
import hashlib
import shutil

assert sys.version_info >= (3, 7)


quiet=False
remove=True
minecraft_version="CHANGEME"
NATIVE_PATH=Path(f"{minecraft_version}-natives")

def get_platform():
    platform=None
    if sys.platform.startswith('freebsd'):
        platform="linux"
    elif sys.platform.startswith('linux'):
        platform="linux"
    elif sys.platform.startswith('aix'):
        platform="linux"
    elif sys.platform.startswith('win32'):
        platform="windows"
    elif sys.platform.startswith('cygwin'):
        platform="windows"
    elif sys.platform.startswith('darwin'):
        platform="osx"
    if platform is None :
        print("Platform is invalid")
        sys.exit(-1)
    return platform
    
PLATFORM=get_platform()

def sha1sum(filename):
    h  = hashlib.sha1()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def download_file(url:str,sha1:str,size:int,path:str,quiet:bool):
    try:
        path=Path(".") / Path(path)
        path=path.absolute()
        if not quiet:
            print(f'Downloading {url.split("/")[-1]}...')
        f = req.urlopen(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb+') as local_file:
            local_file.write(f.read())
        computed_size=Path(path).stat().st_size
        if computed_size!=size:
            print(f"Size error for {path}, {computed_size}!={size}")
            sys.exit(-1)
        computed_sha1=sha1sum(path)
        if computed_sha1!=sha1:
            print(f"Checksum error for {path}, {computed_sha1}!={sha1}")
            sys.exit(-1)
        
    except HTTPError as e:
        if not quiet:
            print('HTTP Error')
            print(e)
        sys.exit(-1)
    except URLError as e:
        if not quiet:
            print('URL Error')
            print(e)
        sys.exit(-1)
        
def process_rules(rules:list):
    keep_going=True
    for rule in rules:
        action=rule["action"]
        if action=="allow":
            if 'os' in rule:
                os=rule['os']
                if 'name' in os:
                    os=os['name']
                if os!=PLATFORM:
                    keep_going=False
        elif action=="disallow":
            if 'os' in rule:
                os=rule['os']
                if 'name' in os:
                    os=os['name']
                if os==PLATFORM:
                    keep_going=False
    return keep_going



if remove:
    jars=sorted(Path('.').glob('**/*.jar'))
    for jar in jars:
        jar.unlink()
    dirs=sorted([el for el in Path('.').iterdir() if el.is_dir()])
    for d in dirs:
        shutil.rmtree(d)

with open(f"{minecraft_version}.json") as file:
    jq=json.load(file)
    #arguments=jq["arguments"]
    #assetIndex=jq["assetIndex"]
    #assets=jq["assets"]
    #complianceLevel=jq["complianceLevel"]
    #downloads=jq["downloads"]
    #ids=jq["id"]
    libs=jq["libraries"]
    #logging=jq["logging"]
    #mainClass=jq["mainClass"]
    #minimumLauncherVersion=jq["minimumLauncherVersion"]
    #releaseTime=jq["releaseTime"]
    #time=jq["time"]
    #types=jq["type"]
    for lib in libs:
        keep_going=True
        if 'rules' in lib.keys():
            rules=lib['rules']
            keep_going=process_rules(rules)
        if not keep_going:
            continue
        native=None
        if 'natives' in lib.keys():
            natives=lib['natives']
            if PLATFORM not in natives:
                print(f"Natives not found in {natives} for platform {PLATFORM}")
                sys.exit(-1)
            native=natives[PLATFORM]

        downloads=lib['downloads']
        if native is not None:
            if "classifiers" not in downloads:
                print(f"Missing classifiers key for {lib['name']}")
                sys.exit(-1)
            classifiers=downloads["classifiers"]
            if native not in classifiers:
                print(f"Missing native key for classifiers {classifiers}")
                sys.exit(-1)
            art=classifiers[native]
            download_file(art["url"],art["sha1"],art["size"],NATIVE_PATH/Path(art["path"]).name,quiet)
        else:
            art=downloads["artifact"]
            if "natives" in art["path"]:
                download_file(art["url"],art["sha1"],art["size"],NATIVE_PATH/Path(art["path"]).name,quiet)
            else:
                download_file(art["url"],art["sha1"],art["size"],art["path"],quiet)
            
