#! /usr/bin/env python

from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Pango
from gi.repository import Notify
import os
import time
import json
import bkup


CONFIGPATH = os.path.join(os.path.expanduser('~'), '.bkup.yaml')
LOGFILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bkuplog.json')

class Indicator:

    def __init__(self):
        self.ind = appindicator.Indicator.new (
                            "Bkup",
                            "brasero-disc-00",
                            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon("brasero-disc-100")

        Notify.init('bkup')

        self.bkup = bkup.Bkup(CONFIGPATH, bkup.Tarsnap())

        # used to check when to remove package file size diff labels
        # also used to check if file size diffs have been calculated
        self.removeDiffLabelTime = 0

        # used to check if backing up is in progress
        self.backingup = False

        # used to store number of archives that are older than 30 days
        # a value of -1 means the number of archives have not been counted
        self.numOldArchives = -1

        self.logFile = LogFile(LOGFILEPATH)

        GObject.timeout_add(60 * 1000, self.updateIconStatus)

        # create the menu
        menu = Gtk.Menu()

        # set a 'title' (disabled menu item)
        self.packageTitle = Gtk.MenuItem('Packages from bkup.yaml:')
        self.packageTitle.set_sensitive(False)
        menu.append(self.packageTitle)

        # create a menu item for each package
        # also store data about each package in self.packages
        self.packages = dict()
        for package in self.bkup.getPackageNames():
            menuItem = Gtk.CheckMenuItem(package)
            self.packages[package] = menuItem
            menuItem.set_active(True)
            menu.append(menuItem)

        # create the backup and diff calc menu items
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)
        
        calculateDiffBtn = Gtk.MenuItem('Calculate File Diffs')
        calculateDiffBtn.connect('activate', self.calculateDiffs)
        menu.append(calculateDiffBtn)

        backupBtn = Gtk.MenuItem('Backup Selected Packages')
        backupBtn.connect('activate', self.backupSelected)
        menu.append(backupBtn)

        # create old archive checking and deleting buttons
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        calculateOldBtn = Gtk.MenuItem('Check Number Of Old Archives')
        calculateOldBtn.connect('activate', self.checkOldArchives)
        menu.append(calculateOldBtn)

        deleteOldBtn = Gtk.MenuItem('Delete archives > 30 days old')
        deleteOldBtn.connect('activate', self.deleteOldArchives)
        menu.append(deleteOldBtn)

        # create unsensitive labels for stats
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        self.lastBackupLabel = Gtk.MenuItem('Last backup: unkown')
        self.lastBackupLabel.set_sensitive(False)
        self.setLastBackupLabel()
        menu.append(self.lastBackupLabel)

        self.lastBackupFileSize = Gtk.MenuItem('Last backup size: unkown')
        self.lastBackupFileSize.set_sensitive(False)
        self.setLastBackupFileSizeLabel()
        menu.append(self.lastBackupFileSize)

        self.totalUsageLabel = Gtk.MenuItem('Total Usage: unkown')
        self.totalUsageLabel.set_sensitive(False)
        self.setTotalUsageLabel()
        menu.append(self.totalUsageLabel)

        self.oldArchivesLabel = Gtk.MenuItem('Archives > 30 days old: unknown')
        self.oldArchivesLabel.set_sensitive(False)
        self.setOldArchivesLabel()
        menu.append(self.oldArchivesLabel)

        # create the quit menu item
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        quitBtn = Gtk.MenuItem('Quit')
        quitBtn.connect('activate', self.closeApp)
        menu.append(quitBtn)

        self.ind.set_menu(menu)
        menu.show_all()

    def updateIcon(self, percentage):
        # percentage is between 0 and 1
        self.ind.set_icon("brasero-disc-" + "%02d" % int(round(percentage, 1) * 100))

    def getSelectedPackages(self):
        selected = []
        for package in self.packages.keys():
            if self.packages[package].get_active():
                selected.append(package)

        return selected

    def backupSelected(self, menuItem):

        if self.removeDiffLabelTime == 0:
            totalDiffs = self.calculateDiffs(None, False)
            if totalDiffs > 50 * 1000000:
                msg = Notify.Notification.new('Selected packages total file change is above 50Mb', 'Click backup selected packages again if you want to ignore this')
                msg.show()
                return False

        self.packageTitle.set_label('backing up...')
        self.setMenuEnabled(False)
        self.backingup = True
        self.updateIconStatus()

        beforeBackupSize = self.bkup.getTotalUsage()

        selected = self.getSelectedPackages()
        success = True

        packageTimes = []
        for package in selected:
            while Gtk.events_pending():
                Gtk.main_iteration()

            self.updateIcon(float(selected.index(package)) / float(len(selected)))

            #TODO: do this in a new thread
            output = self.bkup.backupPackage(package)
            if output != True:
                print('error, breaking from backups')
                print(output)
                self.createErrorDialog(output)
                success = False
                break
            else:
                packageTimes.append({'name': package, 'time': int(time.time())})

        self.packageTitle.set_label('Packages from bkup.yaml:')
        self.setMenuEnabled(True)
        self.updateIcon(0)
        self.removeDiffLabels()
        self.backingup = False

        backupSizeDiff = self.bkup.getTotalUsage() - beforeBackupSize
        self.updateLog(packageTimes, backupSizeDiff)
        
        if success:
            msg = Notify.Notification.new('Selected packages backed up', 'Bkup')
            msg.show()

    def calculateDiffs(self, menuItem, showNotification=True):
        self.setMenuEnabled(False)
        self.packageTitle.set_label('Calculating file diffs...')
        while Gtk.events_pending():
            Gtk.main_iteration()
        selected = self.getSelectedPackages()

        totalDiff = 0

        for package in selected:
            diff = self.bkup.getFileSizeDiff(package)
            totalDiff += diff
            print(self.bkup.humanPrint(diff))
            humanDiff = self.bkup.humanPrint(diff)
            newLabel = package + ' (' + humanDiff + ' change)'
            print(self.packages[package].set_label(newLabel))

        self.setMenuEnabled(True)
        self.packageTitle.set_label('Packages from bkup.yaml:')
        self.removeDiffLabelTime = time.time() + 60 * 5
        GObject.timeout_add(60 * 1000, self.checkDiffLabelRemovalTime)

        if showNotification:
            msg = Notify.Notification.new('Calculated file diffs', 'Bkup')
            msg.show()

        return totalDiff

    def checkOldArchives(self, menuItem, showNotification=True):
        if showNotification:
            msg = Notify.Notification.new('recalculating number of archives older than 30 days', 'Bkup')
            msg.show()

        # TODO: do this in new thread so the user can click other buttons while
        # this is running. Or disable other buttons
        self.oldArchives = self.bkup.filterOld(30)
        self.numOldArchives = len(self.oldArchives)

        if showNotification:
            msg = Notify.Notification.new('Number of archives older than 30 days: ' 
                                          + str(self.numOldArchives))
            msg.show()


        self.setOldArchivesLabel()

        return self.oldArchives

    def deleteOldArchives(self, menuItem):
        if self.numOldArchives > 0:
            msg = Notify.Notification.new('Deleting ' + str(self.numOldArchives)
            + ' archives', 'Bkup')
            msg.show()
            output = self.bkup.deleteArchives(self.oldArchives)
            if output == True:
                msg = Notify.Notification.new('Deleted ' + str(self.numOldArchives)
                + ' archives', 'Bkup')
                msg.show()
                self.numOldArchives = 0
            else:
                self.createErrorDialog(output)
                self.numOldArchives = -1

            setOldArchivesLabel()
        elif self.numOldArchives == 0:
            msg = Notify.Notification.new('No archives older than 30 days', 'Bkup')
            msg.show()
        else:
            self.createErrorDialog('To delete old archives, '
            + 'it is first required to check number of old archives')

    def updateLog(self, packageTimes, backupSize):
        log = self.logFile.read()

        if log == False:
            # log file does not exist
            log = {'packages': {}}

        for package in packageTimes:
            log['packages'][package['name']] = package['time']

        if backupSize > 0:
            log['lastBackupFileSize'] = backupSize

        self.logFile.write(log)

        self.setLastBackupLabel()
        self.setTotalUsageLabel()
        self.setLastBackupFileSizeLabel()
        self.updateIconStatus()

    def setMenuEnabled(self, enable):
        for package in self.packages:
            self.packages[package].set_sensitive(enable)

    def checkDiffLabelRemovalTime(self):
        if self.removeDiffLabelTime < time.time():
            self.removeDiffLabels()
            self.removeDiffLabelTime = 0
            return False

        return True

    def removeDiffLabels(self):
        self.removeDiffLabelTime = 0
        for package in self.packages.keys():
            self.packages[package].set_label(package)

    def setLastBackupLabel(self):
        lastBackupTime = self.logFile.getLastBackupTime()

        if lastBackupTime == False:
            self.lastBackupLabel.set_label('Last: unkown')
        else:
            self.lastBackupLabel.set_label('Last: ' + time.ctime(lastBackupTime))

    def setLastBackupFileSizeLabel(self):
        log = self.logFile.read()

        if type(log) == dict and 'lastBackupFileSize' in log:
            self.lastBackupFileSize.set_label('Last backup size: ' + self.bkup.humanPrint(log['lastBackupFileSize']))
        else:
            self.lastBackupFileSize.set_label('Last backup size: unknown')

    def setTotalUsageLabel(self):
        totalUsage = self.bkup.getTotalUsage()
        if type(totalUsage) == int:
            self.totalUsageLabel.set_label('Total usage: ' + self.bkup.humanPrint(totalUsage))
        else:
            self.totalUsageLabel.set_label('Total usage: unknown')
    
    def setOldArchivesLabel(self):
        if self.numOldArchives != -1:
            self.oldArchivesLabel.set_label('Archives older than 30 days: '
                                            + str(self.numOldArchives))
        else:
            self.oldArchivesLabel.set_label('Archives > 30 days old: unknown')


    def updateIconStatus(self):
        # this function changes the icon status if there has been no backup
        # done within the last 24 hours. This 24 hours is a constant which will
        # be optionally disabled or changed from a config file in the future.

        # this is the only function that should be changing the icon status

        if self.backingup:
            # while backing up, the icon status is active
            self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
            return True

        lastBackupTime = self.logFile.getLastBackupTime()
        remindConstant = 60 * 60 * 24 # 24 hours in seconds

        if lastBackupTime == False:
            return self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

        if lastBackupTime + remindConstant > int(time.time()):
            self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        else:
            self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

        return True
        

    def closeApp(self, menuItem):
        Gtk.main_quit()

    def createErrorDialog(self, errorMsg):
        dialog = Gtk.Dialog(title="Bkup Error", parent=None, flags=0, buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_size(700, 400)
        box = dialog.get_content_area()
        label = Gtk.Label("There was an error with bkup:")
        label.set_alignment(0, 0.5)
        label.set_padding(20, 0)

        textview = Gtk.TextView()
        fontdesc = Pango.FontDescription("monospace 10")
        textview.modify_font(fontdesc)
        textview.set_editable(False)

        textbuf = Gtk.TextBuffer()
        textbuf.set_text(errorMsg)
        textview.set_buffer(textbuf)

        scroll = Gtk.ScrolledWindow()
        scroll.add(textview)
        alignment = Gtk.Alignment()
        alignment.set_padding(0, 10, 20, 20)
        alignment.add(scroll)
        box.pack_start(label, expand=False, fill=False, padding=10)
        box.pack_start(alignment, expand=True, fill=True, padding=0)

        box.show_all()
        dialog.run()
        dialog.destroy()

class LogFile:

    def __init__(self, logPath):
        self.logPath = logPath
    
    def read(self):
        log = True

        try:
            logFile = open(self.logPath)
            log = logFile.read()
            logFile.close()
        except IOError:
            log = False

        if log == False:
            return False

        try:
            log = json.loads(log)
        except:
            log = False

        return log

    def write(self, newLog):
        # newLog should be of type dict as it gets converted to str in this function
        logFile = open(self.logPath, 'w')
        logFile.write(json.dumps(newLog))
        logFile.close()

    def getLastBackupTime(self):
        log = self.read()

        if log == False:
            return False

        biggest = 0
        for packageTime in log['packages'].values():
            if biggest < packageTime:
                biggest = packageTime

        return biggest



if __name__ == "__main__":

    indicator = Indicator()
    Gtk.main()
