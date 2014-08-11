There are three reasons why this was developed over just using cron:
  -  I didn't like the potential of having new large files in my folders that would get unnecessarily backed up and cause the backing up to take much longer than expected.

  - There was also the problem of being on the right connection when backing up. This is mainly due to me being at uni a lot where I have a quota that I would prefer not to use for backing up.

  - Sometimes backing up can take some time to run so I need to be in a place that I wont need to move from while backing up.

Currently, the app will automatically not backup if you click on 'backup selected packages' and you didn't click on 'calculate file diffs' *and* the total difference of all the packages being backed up is over 50Mb. In the future this check will be an option and the limit can be changed. To continue with the backup if this happens, just click on 'backup selected packages' again.

The reason for this extra check is to avoid having to check the file differences manually every single time you backup in case one of the packages has something of a large file size you don't intend to backup.

The icon of the app will change to a brighter colour if there has been no backup in the last 24 hours. This 24 hours is hard coded and cannot yet be changed. Maybe in the future with a config file, the time interval can be changed or disabled.
