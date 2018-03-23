#!/usr/bin/env python3

import argparse
import subprocess
import os.path
import sys
from typing import List


def checkfile(pkglist: List[str], filelist: str) -> str:
    """ adds vmove declarations to a -devel package function
        pkglist -> List of strings that make up the definition up
        untill 'pkg_install() {'
        filelist -> single string that has all files, separated by newline

        it checks for the presence of a path in filelist for each path defined
        in paths, for each match it appends to pkglist a vmove path statement

        it also detects symlinks by parsing over all lines and checking if one
        contains ' -> ', it then splits it and gets the first half and checks
        if it ends with .so .a or .la and if matched it adds a glob vmove
        statement

        to complete the string it adds \t} and } and then returns a string

        TODO: make it deal with .so,.a,.la in places other than /usr/lib
        TODO: make it recieve a list of files instead of a whole string
    """

    solib: bool = False
    alib: bool = False
    lalib: bool = False

    paths: List[str] = ['/usr/include',
                        '/usr/lib/pkgconfig',
                        '/usr/share/pkgconfig',
                        '/usr/lib/cmake',
                        '/usr/share/cmake',
                        '/usr/share/aclocal',
                        '/usr/share/man/man3',
                        '/usr/share/info',
                        '/usr/share/gtk-doc',
                        '/usr/share/gir-1.0',
                        '/usr/share/vala',
                        '/usr/share/doc']

    for path in paths:
        if path in filelist:
            pkglist.append('\t\tvmove %s' % path)

    for line in filelist.split('\n'):
        if ' -> ' in line:
            line = line.split(' -> ', 1)[0]
            if line.endswith('.so') and not solib:
                pkglist.append('\t\tvmove "/usr/lib/*.so"')
                solib = True

            if line.endswith('.a') and not alib:
                pkglist.append('\t\tvmove "/usr/lib/*.a"')
                alib = True

            if line.endswith('.la') and not lalib:
                pkglist.append('\t\tvmove "/usr/lib/*.la"')
                lalib = True

    pkglist.append('\t}')
    pkglist.append('}')

    return '\n'.join(pkglist)


def main():
    p = argparse.ArgumentParser(description="create -devel packages.")
    p.add_argument('develname', metavar='develname', type=str,
                   help='name of the devel package without -devel suffix')
    p.add_argument('pkgname', metavar='pkgname', type=str,
                   help='name of the package to create the devel package')
    p.add_argument('filelist', metavar='filelist', type=str,
                   help='newline separated list of files in main package')
    p.add_argument('-i', dest='replace', action='store_true', default=False,
                   help='replace dependencies in template')

    args = p.parse_args()

    """
        Create a path by taking xdistdir and add srcpkgs/ the pkgname and
        /template
    """
    filepath: str = 'srcpkgs/' + args.pkgname + '/template'
    xdistdir = subprocess.run('xdistdir', stdout=subprocess.PIPE)
    filepath = xdistdir.stdout.decode('utf-8').replace('\n', '/') + filepath

    devname = args.develname + '-devel'

    if not os.path.isfile(filepath):
        print("Invalid filepath: %s" % filepath)
        sys.exit(2)

    pkglist: List[str] = []
    pkglist.append('%s-devel_package() {' % args.develname)
    pkglist.append('\tshort_desc+=" - development files"')
    pkglist.append('\tdepends="%s-${version}_${revision}"' % args.pkgname)
    pkglist.append('\tpkg_install() {')

    if args.replace:
        with open(filepath, 'r') as file_in:
            f = file_in.read()

            if f.find(devname) != -1:
                print('package already made for the name: %s' % devname)
                sys.exit(2)

        file_in.close()

    pkgstring = checkfile(pkglist, args.filelist)

    print(pkgstring)

    if args.replace:
        with open(filepath, "a") as file_out:
            file_out.write(pkgstring)
            file_out.close()


if __name__ == "__main__":
    main()
