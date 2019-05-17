import urllib2
import requests
import os
import platform
import sys
import subprocess

def FAIL(msg,*args,**kwargs):
    if args or kwargs:
        msg = msg.format(*args,**kwargs)
    sys.stderr.write('FAILURE: '+msg)
    sys.exit(1)


if sys.version_info.major != 2:
    FAIL('should only be run using Python 2 for now, as part of the installation...')


afni_bin_url = 'https://afni.nimh.nih.gov/pub/dist/bin/'

afni_dists = '''
linux_openmp
linux_openmp_64
linux_gcc32
linux_gcc33_64
linux_xorg7
linux_xorg7_64
linux_glibc22
linux_fedora_21_64
linux_tiny
macosx_10.5_Intel_64
macosx_10.5_Intel_64icc
macosx_10.6_Intel_64
macosx_10.7_Intel_64
macosx_10.8_gcc
macosx_10.8_icc
NIH.openSUSE.11.4_64
solaris29_suncc
solaris29_suncc_64
'''.strip().split()

afni_dists_redhat = ['linux_openmp_64','linux_openmp']


'''
openmp is preferred.
fedora?  don't care for now.  many versions seem to be ok with openmp anyways?
Intel recommended for mac
don't know if icc (Intel's compiler) is preferable over gcc or unspecified.
xorg then gcc as linux backups.
'''

def makeExecutable(path):
    # Jonathon Reinhart
    # http://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python/30463972#30463972
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)

def getDecon(afni_dist):
    url = afni_bin_url+afni_dist+'/3dDeconvolve'
    req = urllib2.Request(url)
    try:
        res = urllib2.urlopen(req)
    except urllib2.URLError as e:
        print('ERROR: could not access {}'.format(url))
        return False
    
    with open('3dDeconvolve','wb') as f:
        f.write(res.read())
    
    makeExecutable('3dDeconvolve')
    
    if os.system('./3dDeconvolve &> /dev/null'):
        os.remove('3dDeconvolve')
        return False
    
    return True

##testing:
#if getDecon("macosx_10.8_icc"):
#    raise Exception('NO ON NO')

# determine potential 3dDeconvolve binaries
(ver,_,machine) = platform.mac_ver()
if ver:
    # Mac
    ver = ver.split('.')
    if ver[0]!='10':
        FAIL('for Macs, only OS X is supported')
    ver = int(ver[1])
    if ver<5:
        FAIL('unsupported Mac version')
    if ver>=8:
        ver=7 # recommended over 8?  I guess if it works fine...
    pre = 'macosx_10.{}_'.format(ver)
    dists = [d for d in afni_dists if d.startswith(pre)]
else:
    # linux (assuming)
    dists = [d for d in afni_dists if d.startswith('linux')]
    
    
    # redhat doesn't bother to have 64 vs 32 bit info in the dist info?
    # so instead check sys.maxsize
    #if '64' in platform.linux_distribution()[2]:
    if sys.maxsize>2**32:
        dists = [d for d in dists if d.endswith('_64')]
    else:
        dists = [d for d in dists if not d.endswith('_64')]

# try to find an appropriate 3dDeconvolve binary
for dist in dists:
    if getDecon(dist):
        break
else:
    # just try all distributions (slower but more robust)
    print('falling back to other distributions')
    fallback_dists = [dist for dist in afni_dists if '_64' in dist]
    fallback_dists += [dist for dist in afni_dists if '_64' not in dist]
    for dist in fallback_dists:
        if getDecon(dist):
            break
    else:
        FAIL('unable to find an appropriate AFNI distribution')
