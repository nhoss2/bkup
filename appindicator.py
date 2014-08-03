from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Pango
from gi.repository import Notify
import os
import bkup


CONFIGPATH = os.path.join(os.path.expanduser('~'), '.tarsnap.yaml')

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

        GObject.timeout_add(400, self.salad)
        self.iconProgress = 0

        # create the menu
        menu = Gtk.Menu()

        # set a 'title' (disabled menu item)
        menuItem = Gtk.MenuItem('Packages from bkup.yaml:')
        menuItem.set_sensitive(False)
        menu.append(menuItem)

        # create a menu item for each package
        self.packages = dict()
        for package in self.bkup.getPackageNames():
            menuItem = Gtk.CheckMenuItem(package)
            self.packages[package] = menuItem
            menuItem.set_active(True)
            menu.append(menuItem)

        # create the other menu items
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        backupBtn = Gtk.MenuItem('Backup Selected Packages')
        menu.append(backupBtn)

        calculateDiffBtn = Gtk.MenuItem('Calculate File Diffs')
        calculateDiffBtn.connect('activate', self.calculateDiffs)
        menu.append(calculateDiffBtn)

        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        quitBtn = Gtk.MenuItem('Quit')
        quitBtn.connect('activate', self.closeApp)
        menu.append(quitBtn)

        self.ind.set_menu(menu)
        menu.show_all()

    def menuitem_response(self, w, buf):
        print(buf)
        Gtk.main_quit()

    def salad(self):
        #print self.check.get_active()
        if (self.iconProgress == 100):
            self.iconProgress = 0
        else:
            self.iconProgress += 5

        self.ind.set_icon("brasero-disc-" + "%02d" % self.iconProgress)
        #self.ind.set_status(appindicator.IndicatorStatus.PASSIVE)
        return True

    def getSelectedPackages(self):
        selected = []
        for package in self.packages.keys():
            if self.packages[package].get_active():
                selected.append(package)

        return selected

    def calculateDiffs(self, menuItem):
        selected = self.getSelectedPackages()
        for package in selected:
            diff = self.bkup.getFileSizeDiff(package)
            print self.bkup.humanPrint(diff)
            humanDiff = self.bkup.humanPrint(diff)
            newLabel = package + ' (' + humanDiff + ' change)'
            print self.packages[package].set_label(newLabel)


        GObject.timeout_add(5 * 60 * 1000, self.removeDiffLabels)
        msg = Notify.Notification.new('bkup', 'Calculated File Diffs')
        msg.show()

    def removeDiffLabels(self):
        for package in self.packages.keys():
            self.packages[package].set_label(package)

        
    def closeApp(self, menuItem):
        Gtk.main_quit()

    def createErrorDialog(self):
        dialog = Gtk.Dialog(title="Bkup Error", parent=None, flags=0, buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_size(700, 400)
        box = dialog.get_content_area()
        label = Gtk.Label("There was an error:")
        label.set_alignment(0, 0.5)
        label.set_padding(20, 0)

        textview = Gtk.TextView()
        fontdesc = Pango.FontDescription("monospace 10")
        textview.modify_font(fontdesc)
        textview.set_editable(False)

        textbuf = Gtk.TextBuffer()
        textbuf.set_text("This is the error ey")
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
