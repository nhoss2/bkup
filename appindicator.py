from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Pango
from gi.repository import Notify
import os
import time
import json
import bkup


CONFIGPATH = os.path.join(os.path.expanduser('~'), '.tarsnap.yaml')
LOGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bkuplog.json')

class Indicator:

    def __init__(self):
        self.ind = appindicator.Indicator.new (
                            "Bkup",
                            "brasero-disc-00",
                            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon ("indicator-messages-new")

        Notify.init('bkup')

        self.bkup = bkup.Bkup(CONFIGPATH, bkup.Tarsnap())

        # used to check when to remove package file size diff labels
        # also used to check if file size diffs have been calculated
        self.removeDiffLabelTime = 0

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

        # create the last backup label
        self.lastBackupLabel = Gtk.MenuItem('Last backup: unkown')
        self.lastBackupLabel.set_sensitive(False)
        self.setLastBackupLabel()
        menu.append(self.lastBackupLabel)

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
                print 'error, breaking from backups'
                print output
                self.createErrorDialog(output)
                success = False
                break
            else:
                packageTimes.append({'name': package, 'time': int(time.time())})

        self.packageTitle.set_label('Packages from bkup.yaml:')
        self.setMenuEnabled(True)
        self.updateIcon(0)
        self.removeDiffLabels()
        self.setLastBackupLabel()

        self.updateLog(packageTimes)
        
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
            print self.bkup.humanPrint(diff)
            humanDiff = self.bkup.humanPrint(diff)
            newLabel = package + ' (' + humanDiff + ' change)'
            print self.packages[package].set_label(newLabel)

        self.setMenuEnabled(True)
        self.packageTitle.set_label('Packages from bkup.yaml:')
        self.removeDiffLabelTime = time.time() + 60 * 5
        GObject.timeout_add(60 * 1000, self.checkDiffLabelRemovalTime)

        if showNotification:
            msg = Notify.Notification.new('Calculated file diffs', 'Bkup')
            msg.show()

        return totalDiff

    def updateLog(self, packageTimes):
        try:
            logFile = open(LOGFILE)
            log = json.loads(logFile.read())
            logFile.close()
        except IOError:
            log = {'packages': {}}

        for package in packageTimes:
            log['packages'][package['name']] = package['time']

        logFile = open(LOGFILE, 'w')
        logFile.write(json.dumps(log))
        logFile.close()

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
        try:
            logFile = open(LOGFILE)
            log = json.loads(logFile.read())
            logFile.close()
        except IOError:
            log = False

        if log == False:
            self.lastBackupLabel.set_label('Last backup: unkown')
        else:
            biggest = 0
            for packageTime in log['packages'].values():
                if biggest < packageTime:
                    biggest = packageTime

            self.lastBackupLabel.set_label('Last: ' + time.ctime(biggest))


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


if __name__ == "__main__":

    indicator = Indicator()
    Gtk.main()
