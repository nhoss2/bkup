Bkup
====

An ubuntu app indicator for tarsnap backups. Works by defining 'packages' of paths to backup which you can then manually select to have backed up.

installation
------------

This isn't ready for use yet. If you want to try it out though, clone this repo, create a `~/.bkup.yaml` file and run `python appindicator.py`. You need to have tarsnap installed and set up.

example bkup.yaml
-----------------

.bkup.yaml needs to be in your home directory
    
    name-of-package:
      include:
        - /full/path/to/backup
        - /some/other/path
      exclude:
        - /anything/to/exclude

    another-package:
      include:
        - /home/nafis/.vim
        - /home/nafis/.vimrc

    code:
      include:
        - /home/nafis/code
        - /home/nafis/work
      exclude:
        - /home/nafis/code/bigproject/libraries
        - /home/nafis/code/chromium-clone


motivations
-----------

There are three reasons why this was developed over just using something like cron:

  -  I didn't like the potential of having new large files in my folders that would get unnecessarily backed up and cause the backing up to take much longer than expected.

  - There was also the problem of being on the right connection when backing up. This is mainly due to me being at uni a lot where I have a quota that I would prefer not to use for backing up.

  - Sometimes backing up can take some time to run so I need to be in a place that I wont need to move from while backing up.


things to note
--------------

  - Currently, the app will automatically not backup if you click on 'backup selected packages' and you didn't click on 'calculate file diffs' **and** the total difference of all the packages being backed up is over 50Mb. In the future this check will be an option and the limit can be changed. To continue with the backup if this happens, just click on 'backup selected packages' again.
   
    The reason for this extra check is to avoid having to check the file differences manually every single time you backup in case one of the packages has something of a large file size you don't intend to backup.
   
  - The icon of the app will change to a brighter colour if there has been no backup in the last 24 hours. This 24 hours is hard coded and cannot yet be changed. Maybe in the future with a config file, the time interval can be changed or disabled.

  - Each package backed up will be in the format: `packageName:yyyy-m-dd#unixtime`. eg: `nuclearplans:2014-8-4#1407148246`. So don't have `:` or `#` in your package names.


roadmap
-------

  - View details about each package backed up
  - Delete backups
  - Duplicity support


licence
-------

The MIT License (MIT)

Copyright (c) 2014 Nafis Hossain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
