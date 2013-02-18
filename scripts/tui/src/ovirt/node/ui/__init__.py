#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# __init__.py - Copyright (C) 2012 Red Hat, Inc.
# Written by Fabian Deutsch <fabiand@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
from ovirt.node import base

"""
This contains abstract UI Elements
"""


# http://stackoverflow.com/questions/739654/understanding-python-decorators
class Element(base.Base):
    """An abstract UI Element.
    This basically provides signals to communicate between real UI widget and
    the plugins
    """
    path = None
    on_value_change = None

    def __init__(self, path=None):
        """Registers all widget signals.
        All signals must be given in self.signals
        """
        super(Element, self).__init__()
        self.path = path
        self.on_value_change = self.new_signal()
        self.logger.debug("Initializing %s" % self)

    def value(self, value=None):
        """A general way to set the "value" of a widget
        Can be a text or selection, ...
        """
        raise NotImplementedError

    def elements(self):
        return [self]

    def __repr__(self):
        return "<%s path='%s' at %s>" % (self.__class__.__name__, self.path,
                                         hex(id(self)))


class InputElement(Element):
    """An abstract UI Element for user input
    on_change:
        To be called by the consumer when the associated widget changed

    on_enabled_change:
        Called by the Element when enabled changes
    """
    on_change = None

    on_enabled_change = None
    on_valid_change = None

    def __init__(self, path, is_enabled):
        super(InputElement, self).__init__(path)
        self.on_enabled_change = self.new_signal()
        self.on_change = self.new_signal()
        self.on_valid_change = self.new_signal()
        self.enabled(is_enabled)
        self.text("")
        self.valid(True)

        self.on_change.connect(ChangeAction())

    def enabled(self, is_enabled=None):
        if is_enabled in [True, False]:
            self.on_enabled_change(is_enabled)
            self._enabled = is_enabled
        return self._enabled

    def valid(self, is_valid):
        if is_valid in [True, False]:
            self.on_value_change(is_valid)
            self._valid = is_valid
        return self._valid

    def text(self, text=None):
        if text is not None:
            self.on_value_change(text)
            self._text = text
        return self._text

    def value(self, txt=None):
        return self.text(txt)


class ContainerElement(Element):
    """An abstract container Element containing other Elements
    """
    children = []
    title = None

    def __init__(self, path, children, title=None):
        super(ContainerElement, self).__init__(path)
        self.children = children
        self.title = title

    def elements(self):
        """Retrieve all Elements in this Element-Tree in a flat dict
        Returns:
            dict of mapping (path, element)
        """
        elements = [self]
        for element in self.children:
            elements += element.elements()
        return elements

    def __getitem__(self, path):
        return {c.path: c for c in self.children}[path]


class Action(base.Base):
    callback = None

    def __init__(self, callback=None):
        super(Action, self).__init__()
        self.callback = callback

    def __call__(self, target, userdata=None):
        r = None
        if self.callback:
            self.logger.debug("Calling action %s %s with %s" % (self,
                                                                self.callback,
                                                                userdata))
            r = self.callback(userdata)
            self.logger.debug("Action %s called and returned: %s" % (self, r))
        else:
            self.logger.warning("No callback for %s" % self)
        return r

    def __str__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.callback)


class ChangeAction(Action):
    """Action to validate the current change
    """
    pass


class SaveAction(Action):
    """Action to save the current page/dialog
    """
    pass


class CloseAction(Action):
    """Action to close the current/given dialog

    Args:
        dialog: The dialog to close
    """
    dialog = None

    def __init__(self, callback=None, dialog=None):
        super(CloseAction, self).__init__(callback)
        self.dialog = dialog


class ResetAction(Action):
    """Action to reset all InputElements on the current page/dialog
    """
    pass


class ReloadAction(Action):
    """Action to reload the current page/dialog
    """
    pass


class QuitAction(Action):
    """Action to quit the application
    """
    pass


class Row(ContainerElement):
    """Align elements horizontally in one row
    """
    pass


class Label(Element):
    """Represents a r/o label
    """

    def __init__(self, path, text):
        super(Label, self).__init__(path)
        self.text(text)

    def text(self, text=None):
        if text is not None:
            self.on_value_change(text)
            self._text = text
        return self._text

    def value(self, txt=None):
        return self.text(txt)


class Header(Label):
    template = "\n  %s\n"

    def __init__(self, path, text, template=template):
        super(Header, self).__init__(path, text)
        self.template = template


class KeywordLabel(Label):
    """A label consisting of a prominent keyword and a value.
    E.g.: <b>Networking:</b> Enabled
    """

    def __init__(self, path, keyword, text=""):
        super(KeywordLabel, self).__init__(path, text)
        self.keyword = keyword


class Entry(InputElement):
    """Represents an entry field
    TODO multiline

    Args:
        on_valid_change: Is emitted by this clas when the value of valid
                         changes e.g. when a plugin is changing it.
    """

    def __init__(self, path, label, enabled=True, align_vertical=False):
        super(Entry, self).__init__(path, enabled)
        self.label = label
        self.align_vertical = align_vertical


class PasswordEntry(Entry):
    pass


class Button(InputElement):
    """A button can be used to submit or save the current page/dialog
    There are several derivatives which are "shortcuts" to launch a specific
    action.

    Args:
        on_activate: The signal shall be called by the toolkit implementing the
                     button, when the button got "clicked"
    """
    on_activate = None

    def __init__(self, path, label, enabled=True):
        """Constructor

        Args:
            path: Path within the model
            label: Label of the button
            enabled: If the button is enabled (can be clicked)
        """
        super(Button, self).__init__(path, enabled)
        self.text(label)
        self.label(label)

        self.on_activate = self.new_signal()
        self.on_activate.connect(ChangeAction())
        self.on_activate.connect(SaveAction())

    def label(self, label=None):
        """Can be used to retrieve or change the label
        """
        if label is not None:
            self.on_value_change(label)
            self._label = label
        return self._label

    def value(self, value=None):
        self.label(value)


class SaveButton(Button):
    """This derived class is primarily needed to allow an easy disabling of the
    save button when the changed data is invalid.
    """
    def __init__(self, path, label="Save", enabled=True):
        super(SaveButton, self).__init__(path, label, enabled)


class ResetButton(Button):
    """This button calls the ResetAction to reset all UI data to the current
    model, discrading all pending changes.
    """
    def __init__(self, path, label="Reset", enabled=True):
        super(ResetButton, self).__init__(path, label, enabled)
        self.on_activate.clear()
        self.on_activate.connect(ResetAction())
        self.on_activate.connect(ReloadAction())


class CloseButton(Button):
    """The close button can be used to close the top-most dialog
    """
    def __init__(self, path, label="Close", enabled=True):
        super(CloseButton, self).__init__(path, label, enabled)
        self.on_activate.clear()
        self.on_activate.connect(CloseAction())


class QuitButton(Button):
    """The quit button can be used to quit the whole application
    """
    def __init__(self, path, label="Quit", enabled=True):
        super(QuitButton, self).__init__(path, label, enabled)
        self.on_activate.clear()
        self.on_activate.connect(QuitAction())


class Divider(Element):
    """A divider can be used to add some space between UI Elements.

    Args:
        char: A (optional) char to be used as a separator
    """
    def __init__(self, path, char=u" "):
        super(Divider, self).__init__(path)
        self.char = char


class Options(InputElement):
    """A selection of options

    Args:
        label: The caption of the options
        options:
    """

    def __init__(self, path, label, options, selected=None):
        super(Options, self).__init__(path, True)
        self.label = label
        self.options = options
        self.option(selected or options[0][0])

    def option(self, option=None):
        if option in dict(self.options).keys():
            self.on_value_change(option)
            self._option = option
        return self._option

    def value(self, value=None):
        return self.option(value)


class Checkbox(InputElement):
    """A simple Checkbox

    Args:
        label: Caption of this checkbox
        state: The initial change
    """

    def __init__(self, path, label, state=False, is_enabled=True):
        super(Checkbox, self).__init__(path, is_enabled)
        self.label = label
        self.state(state)

    def state(self, s=None):
        if s in [True, False]:
            self.on_value_change(s)
            self._state = s
        return self._state

    def value(self, value=None):
        return self.state(value)


class ProgressBar(Element):
    """A abstract progress bar.

    Args:
        current: The initial value
        done: The maximum value
    """
    def __init__(self, path, current=0, done=100):
        super(ProgressBar, self).__init__(path)
        self.current(current)
        self.done = done

    def current(self, current=None):
        """Get/Set the current status

        Args:
            current: New value or None

        Returns:
            The current progress
        """
        if current is not None:
            self.on_value_change(current)
            self._current = current
        return self._current

    def value(self, value):
        return self.current(value)


class Table(InputElement):
    """Represents a simple Table with one column

    Args:
        header: A string
        items: A list of tuples (key, label)
        height: The height of the Table
    """
    on_activate = None

    def __init__(self, path, label, header, items, selected_item=None,
                 height=5, enabled=True):
        super(Table, self).__init__(path, enabled)
        self.label = label
        self.header = header
        self.items = items
        self.height = height
        self.select(selected_item or items[0][0])
        self.on_activate = self.new_signal()
        self.on_activate.connect(SaveAction())

    def select(self, selected=None):
        if selected in dict(self.items).keys():
            self.on_value_change(selected)
            self._selected = selected
        return self._selected

    def value(self, value=None):
        self.select(value)


class Window(Element):
    """Abstract Window definition
    """

    application = None

    __hotkeys_enabled = True

    def __init__(self, path, application):
        super(Window, self).__init__(path=path)
        self.logger.info("Creating UI for application '%s'" % application)
        self.application = application

        self._plugins = {}
        self._hotkeys = {}

        self.footer = None

        self.navigate = Window.Navigation(self.application)

    def register_plugin(self, title, plugin):
        """Register a plugin to be shown in the UI
        """
        if title in self._plugins:
            raise RuntimeError("Plugin with same path is " +
                               "already registered: %s" % title)
        self._plugins[title] = plugin

    def hotkeys_enabled(self, new_value=None):
        """Disable all attached hotkey callbacks

        Args:
            new_value: If hotkeys shall be enabled or disabled

        Returns:
            If the hotkeys are enabled or disabled
        """
        if new_value in [True, False]:
            self.__hotkeys_enabled = new_value
        return self.__hotkeys_enabled

    def register_hotkey(self, hotkey, cb):
        """Register a hotkey

        Args:
            hotkeys: The key combination (very vague ...) triggering the
                     callback
             cb: The callback to be called
        """
        if type(hotkey) is str:
            hotkey = [hotkey]
        self.logger.debug("Registering hotkey '%s': %s" % (hotkey, cb))
        self._hotkeys[str(hotkey)] = cb

    def _show_on_page(self, page):
        """Shows the ui.Page as on a dialog.
        """
        raise NotImplementedError

    def _show_on_dialog(self, dialog):
        """Shows the ui.Dialog as on a dialog.
        """
        raise NotImplementedError

    def close_dialog(self, dialog):
        """Close the ui.Dialog
        """
        raise NotImplementedError

    def suspended(self):
        """Supspends the screen to do something in the foreground
        Returns:
            ...
        """
        raise NotImplementedError

    def force_redraw(self):
        """Forces a complete redraw of the UI
        """
        raise NotImplementedError

    class Navigation(base.Base):
        """A convenience class to navigate through a window
        """

        application = None

        def __init__(self, application):
            self.application = application
            super(Window.Navigation, self).__init__()

        def index(self):
            plugins = self.application.plugins().items()
            get_rank = lambda path_plugin: path_plugin[1].rank()
            self.logger.debug("Available plugins: %s" % plugins)
            sorted_plugins = [p for n, p in sorted(plugins, key=get_rank)
                              if p.has_ui()]
            self.logger.debug("Available plugins with ui: %s" % sorted_plugins)
            return sorted_plugins

        def to_plugin(self, plugin_candidate):
            """Goes to the plugin (by instance or type)
            Args
                idx: The plugin instance/type to go to
            """
            self.logger.debug("Navigating to plugin %s" % plugin_candidate)
            self.application.switch_to_plugin(plugin_candidate)
            self.logger.debug("Navigated to plugin %s" % plugin_candidate)

        def to_nth(self, idx, is_relative=False):
            """Goes to the plugin (by idx)
            Any pending changes are ignored.

            Args
                idx: The plugin idx to go to
            """
            plugins = self.index()
            self.logger.debug("Switching to page %s (%s)" % (idx, plugins))
            if is_relative:
                idx += plugins.index(self.application.current_plugin())
            plugin = plugins[idx]
            self.to_plugin(plugin)

        def to_next_plugin(self):
            """Goes to the next plugin, based on the current one
            """
            self.to_nth(1, True)

        def to_previous_plugin(self):
            """Goes to the previous plugin, based on the current one
            """
            self.to_nth(-1, True)

        def to_first_plugin(self):
            """Goes to the first plugin
            """
            self.to_nth(0)

        def to_last_plugin(self):
            """Goes to the last plugin
            """
            self.to_nth(-1)


class Page(ContainerElement):
    """An abstract page with a couple of widgets
    """
    buttons = []

    def __init__(self, path, children, title=None):
        super(Page, self).__init__(path, children, title)
        self.buttons = self.buttons or [SaveButton("%s.save" % path),
                                        ResetButton("%s.reset" % path)
                                        ]

    def elements(self):
        return super(Page, self).elements() + self.buttons


class Dialog(Page):
    """An abstract dialog, similar to a page
    """

    escape_key = "esc"
    on_close = None

    def __init__(self, path, title, children):
        super(Dialog, self).__init__(path, children, title)
        self.on_close = self.new_signal()
        self.close(False)
        self.on_close.connect(CloseAction(dialog=self))

    def close(self, v=True):
        if v:
            self.on_close(self)


class TransactionProgressDialog(Dialog):
    """Display the progress of a transaction in a dialog
    """

    def __init__(self, path, transaction, plugin, initial_text=""):
        self.transaction = transaction
        self.texts = [initial_text, ""]
        self.plugin = plugin

        self._close_button = CloseButton("button.close")
        self.buttons = [self._close_button]
        self._progress_label = Label("dialog.progress", initial_text)
        widgets = [self._progress_label]
        title = "Transaction: %s" % self.transaction.title
        super(TransactionProgressDialog, self).__init__(path,
                                                        title,
                                                        widgets)

    def add_update(self, txt):
        self.texts.append(txt)
        self._progress_label.text("\n".join(self.texts))

    def run(self):
        self.plugin.application.show(self)
        self._close_button.enabled(False)
        if self.transaction:
            self.logger.debug("Initiating transaction")
            self.__run_transaction()
        else:
            self.add_update("There were no changes, nothing to do.")
        self._close_button.enabled(True)

    def __run_transaction(self):
        try:
            self.add_update("Checking pre-conditions ...")
            for idx, tx_element in self.transaction.step():
                txt = "(%s/%s) %s" % (idx + 1, len(self.transaction),
                                      tx_element.title)
                self.add_update(txt)
                self.plugin.dry_or(lambda: tx_element.commit())
            self.add_update("\nAll changes were applied successfully.")
        except Exception as e:
            self.add_update("\nAn error occurred while applying the changes:")
            self.add_update("%s" % e)


class AbstractUIBuilder(base.Base):
    """An abstract class
    """
    application = None

    def __init__(self, application):
        super(AbstractUIBuilder, self).__init__()
        self.application = application

    def build(self, ui_element):
        assert Element in type(ui_element).mro()

        builder_for_element = {
            Window: self._build_window,
            Page: self._build_page,
            Dialog: self._build_dialog,

            Label: self._build_label,
            KeywordLabel: self._build_keywordlabel,

            Entry: self._build_entry,
            PasswordEntry: self._build_passwordentry,

            Header: self._build_header,

            Button: self._build_button,

            Options: self._build_options,
            ProgressBar: self._build_progressbar,
            Table: self._build_table,
            Checkbox: self._build_checkbox,

            Divider: self._build_divider,
            Row: self._build_row,
        }

        self.logger.debug("Building %s" % ui_element)

        ui_element_type = type(ui_element)
        builder_func = None

        # Check if builder is available for UI Element
        if ui_element_type in builder_for_element:
            builder_func = builder_for_element[ui_element_type]
        else:
            # It could be a derived type, therefor find it's base:
            for sub_type in type(ui_element).mro():
                if sub_type in builder_for_element:
                    builder_func = builder_for_element[sub_type]

        if not builder_func:
            raise Exception("No builder for UI element '%s'" % ui_element)

        # Build widget from UI Element
        widget = builder_func(ui_element)

        # Give the widget the ability to also use the ui_builder
        widget._ui_builder = self

        return widget

    def _build_window(self, ui_window):
        raise NotImplementedError

    def _build_page(self, ui_page):
        raise NotImplementedError

    def _build_dialog(self, ui_dialog):
        raise NotImplementedError

    def _build_label(self, ui_label):
        raise NotImplementedError

    def _build_keywordlabel(self, ui_keywordlabel):
        raise NotImplementedError

    def _build_header(self, ui_header):
        raise NotImplementedError

    def _build_button(self, ui_button):
        raise NotImplementedError

    def _build_button_bar(self, ui_button):
        raise NotImplementedError

    def _build_entry(self, ui_entry):
        raise NotImplementedError

    def _build_passwordentry(self, ui_passwordentry):
        raise NotImplementedError

    def _build_divider(self, ui_divider):
        raise NotImplementedError

    def _build_options(self, ui_options):
        raise NotImplementedError

    def _build_checkbox(self, ui_checkbox):
        raise NotImplementedError

    def _build_progressbar(self, ui_progressbar):
        raise NotImplementedError

    def _build_table(self, ui_table):
        raise NotImplementedError

    def _build_row(self, ui_row):
        raise NotImplementedError
