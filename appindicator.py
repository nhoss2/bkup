from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Pango
import time

class Indicator:

    def __init__(self):
        self.ind = appindicator.Indicator.new (
                            "example-simple-client",
                            "brasero-disc-00",
                            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon ("indicator-messages-new")

        GObject.timeout_add(100, self.salad)

        self.iconProgress = 0

        # create a menu
        menu = Gtk.Menu()

        # create some 
        for i in range(3):
            buf = "Test-undermenu - %d" % i


            if i == 1:
                print i
                sep = Gtk.SeparatorMenuItem()
                menu.append(sep)
                sep.show()
                check = Gtk.CheckMenuItem('test check item')
                check.show()
                self.check = check
                menu.append(check)

            menu_items = Gtk.MenuItem(buf)

            menu.append(menu_items)

            # this is where you would connect your menu item up with a function:
            menu_items.connect("activate", self.menuitem_response, buf)

            # show the items
            menu_items.show()

        self.ind.set_menu(menu)

    def menuitem_response(self, w, buf):
        print(buf)
        dialog = Gtk.Dialog(title="ey", parent=None, flags=0, buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        dialog.set_default_size(500, 500)
        box = dialog.get_content_area()
        textview = Gtk.TextView()
        fontdesc = Pango.FontDescription("monospace 10")
        textview.modify_font(fontdesc)
        scroll = Gtk.ScrolledWindow()
        #scroll.show()
        scroll.add(textview)
        box.add(scroll)
        box.show_all()
        response = dialog.run()
        dialog.destroy()
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


if __name__ == "__main__":

    indicator = Indicator()
    Gtk.main()
