import re
import platform
from decimal import Decimal
from urllib import quote

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

from electrum_ltc_gui.qt.qrcodewidget import QRCodeWidget

from electrum_ltc import bmp, pyqrnative, BasePlugin
from electrum_ltc.i18n import _


if platform.system() == 'Windows':
    MONOSPACE_FONT = 'Lucida Console'
elif platform.system() == 'Darwin':
    MONOSPACE_FONT = 'Monaco'
else:
    MONOSPACE_FONT = 'monospace'

column_index = 4

class QR_Window(QWidget):

    def __init__(self, exchanger):
        QWidget.__init__(self)
        self.exchanger = exchanger
        self.setWindowTitle('Electrum - '+_('Prypto Redemption'))
        self.setMinimumSize(800, 250)
        self.address = ''
        self.label = ''
        self.amount = 0
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        main_box = QHBoxLayout()
        
        self.qrw = QRCodeWidget()
        main_box.addWidget(self.qrw, 1)

        vbox = QVBoxLayout()
        main_box.addLayout(vbox)

        self.address_label = QLabel("")
        #self.address_label.setFont(QFont(MONOSPACE_FONT))
        vbox.addWidget(self.address_label)

        self.label_label = QLabel("")
        vbox.addWidget(self.label_label)

        self.amount_label = QLabel("")
        vbox.addWidget(self.amount_label)

        vbox.addStretch(1)
        self.setLayout(main_box)


    def set_content(self, addr, label, amount, currency):
        self.address = addr
        address_text = "<span style='font-size: 18pt'>%s</span>" % addr if addr else ""
        self.address_label.setText(address_text)

        if currency == 'MYR': currency = None
        amount_text = ''
        if amount:
            if currency:
                try:
                    self.amount = Decimal(amount) / self.exchanger.exchange(1, currency) if currency else amount
                except Exception:
                    self.amount = None
            else:
                self.amount = Decimal(amount)
            self.amount = self.amount.quantize(Decimal('1.0000'))

            if currency:
                amount_text += "<span style='font-size: 18pt'>%s %s</span><br/>" % (amount, currency)
            amount_text += "<span style='font-size: 21pt'>%s</span> <span style='font-size: 16pt'>MYR</span> " % str(self.amount) 
        else:
            self.amount = None
            
        self.amount_label.setText(amount_text)

        self.label = label
        label_text = "<span style='font-size: 21pt'>%s</span>" % label if label else ""
        self.label_label.setText(label_text)

        msg = 'myriadcoin:'+self.address
        if self.amount is not None:
            msg += '?amount=%s'%(str( self.amount))
            if self.label is not None:
                encoded_label = quote(self.label)
                msg += '&label=%s'%(encoded_label)
        elif self.label is not None:
            encoded_label = quote(self.label)
            msg += '?label=%s'%(encoded_label)
            
        self.qrw.set_addr( msg )




class Plugin(BasePlugin):

    def fullname(self):
        return 'Prypto Redemption Window'

    def description(self):
        return _('Redeem Prypto ScratchCards Here.')

    def init(self):
        self.window = self.gui.main_window
        self.wallet = self.window.wallet

        self.qr_window = None
        
        self.window.expert_mode = True
        self.window.receive_list.setColumnCount(5)
        self.window.receive_list.setHeaderLabels([ _('Address'), _('Label'), _('Balance'), _('Tx'), _('Request')])
        self.requested_amounts = {}
      

    def enable(self):
        return BasePlugin.enable(self)


    def close(self):
        self.window.receive_list.setHeaderLabels([ _('Address'), _('Label'), _('Balance'), _('Tx')])
        self.window.receive_list.setColumnCount(4)
        for i,width in enumerate(self.window.column_widths['receive']):
            self.window.receive_list.setColumnWidth(i, width)
        self.toggle_QR_window(False)

'''
1) @param MToken   # Your merchant token
2) @param Coin     # With what coin does your customer pay
3) @param Code     # The Crypto Scratch Card code
4) @param SKey     # The Crypto Scratch Card security code
5) @param Address  # The address where you want to receive the payment
   @return         #Returns the transaction id if successful, else it will return null.
'''

def credit(Coin, Code, SKey, Address):
    url = "https://prypto.com/merchants/api/?T=RX&TKN={}&COIN={}&PC={}&SC={}&RX={}".format(PRYPTO_KEY, Coin, Code, SKey, Address)
    data = urllib2.urlopen(url)
    response = data.read()
    if response != None and len(response) == 64:
        return response
    else:
        return False
