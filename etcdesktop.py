#!/usr/bin/env python3

# Copyright (C) 2016 Ikey Doherty
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
import threading
import time
import os

import gi.repository
import requests
from gi.repository import Budgie, GObject, Gtk, Gdk

gi.require_version('Budgie', '1.0')
gi.require_version('Wnck', '3.0')


class etcDesktop(GObject.GObject, Budgie.Plugin):
    """ This is simply an entry point into your Budgie Applet implementation.
        Note you must always override Object, and implement Plugin.
    """

    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "etcDesktop"

    def __init__(self):
        """ Initialisation is important.
        """
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        """ This is where the real fun happens. Return a new Budgie.Applet
            instance with the given UUID. The UUID is determined by the
            BudgiePanelManager, and is used for lifetime tracking.
        """
        return etcDesktopApplet(uuid)


class etcDesktopApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """

    label = None
    popover = None

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self.manager = None
        # Add a button to our UI
        self.box = Gtk.EventBox()
        self.label = Gtk.Label('etc: ')
        self.label.set_margin_start(6)
        self.label.set_margin_end(6)
        self.box.add(self.label)
        self.add(self.box)

        self.popover = Budgie.Popover.new(self.box)
        self.popover.get_style_context().add_class("ETC-popover")

        layout = Gtk.Grid()
        layout.set_border_width(6)

        self.highlabel = Gtk.Label(_("High(24h): "))
        layout.attach(self.highlabel, 0, 2, 2, 2)
        self.lowlabel = Gtk.Label(_("Low(24h): "))
        layout.attach(self.lowlabel, 0, 4, 2, 2)

        # layout.add(self.lowlabel)
        self.popover.add(layout)
        self.popover.get_child().show_all()
        self.show_all()
        self.box.connect("button-press-event", self._on_press)
        t = myThread(self.label, self.highlabel, self.lowlabel)
        t.start()
    def do_update_popovers(self, manager):
        """Register popover to manager"""
        manager.register_popover(self.box, self.popover)
        self.manager = manager

    def	_on_press(self, box, e):
        if e.button != 1:
            return Gdk.EVENT_PROPAGATE

        # Popover show and hide
        if self.popover.get_visible():
            self.popover.hide()
        else:
            self.manager.show_popover(self.box)
        return Gdk.EVENT_STOP



class myThread (threading.Thread):
    def __init__(self, label, highlabel, lowlabel):
        threading.Thread.__init__(self)
        self.label = label
        self.highlabel = highlabel
        self.lowlabel = lowlabel
        dirname, filename = os.path.split(os.path.abspath(__file__))
        self.user_data = json.load(open(dirname + '/settings.json'))

    def run(self):
            while True:
                data = self.getData()
                if data is not False:
                    data_keys = list(data['result'].keys())
                    self.label.set_text("{0}: €{1}".format(
                        self.user_data['name'],
                        data['result'][data_keys[0]]['b'][0][:-5])
                        )
                    self.highlabel.set_text("High(24h): €{0}".format(
                        data['result'][data_keys[0]]['h'][1][:-5])
                        )
                    self.lowlabel.set_text("Low(24h): €{0}".format(
                        data['result'][data_keys[0]]['l'][1][:-5])
                        )
                else:
                    self.label.set_text("Failed to load data")

                time.sleep(self.user_data['timeout'])

    def getData(self):
        try:
            response = requests.request("GET", 'https://api.kraken.com/0/public/Ticker?pair=' + self.user_data['pair'])
            json_obj = json.loads(response.text)
            return json_obj
        except ValueError:
            return False
        except Exception:
             return False
