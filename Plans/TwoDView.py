import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di
import guidata.dataset.qtwidgets as wid
import guidata
import qtawesome as qta

from pyqtgraph import PlotWidget
from qtpy.QtWidgets import QWidget, QHBoxLayout, QSpacerItem, QSizePolicy, QVBoxLayout




#class Settings(dt.DataSet):
#    cur_T = di.FloatItem('Curr t')
#    cur_Tidx = di.FloatItem('Min Step')


class W(QWidget):
    def __init__(self):
        super().__init__()
        self.s = Settings()
        lay = QVBoxLayout()
        self.setLayout(lay)
        w = wid.DataSetEditGroupBox('Settings', Settings, button_icon=qta.icon('fa.check'))
        #w.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        lay.addWidget(w)
        lay.addStretch()
if __name__ == '__main__':
    app = guidata.qapplication()

    from qt_material import apply_stylesheet
    apply_stylesheet(app, 'light_blue.xml')
    s = W()
    s.show()
    app.exec_()
