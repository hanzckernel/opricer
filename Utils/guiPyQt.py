import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)


class Window(QtWidgets.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.initUI()

    def initUI(self):
        # print(QtCore.QFile.exists('markt.png'))
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("PyQT tuts!")
        # self.setWindowIcon(QtGui.QIcon('markt.png'))

        extractAction = QtWidgets.QAction(' &Exit', self)
        extractAction.setShortcut('Ctrl+Q')
        extractAction.setStatusTip('Leave the App')
        extractAction.triggered.connect(self.close_app)

        # mainMenu = self.menuBar()
        # fileMenu = mainMenu.addMenu(' &File')
        # fileMenu.addAction(extractAction)

        self.home()

    def home(self):
        btn = QtWidgets.QPushButton("Quit", self)
        btn.clicked.connect(self.close_app)
        btn.move(0, 100)
        btn.resize(btn.sizeHint())

        extractAction = QtWidgets.QAction(
            QtGui.QIcon('batoon.jpg'), 'Flee!', self)
        extractAction.triggered.connect(self.close_app)

        self.toolBar = self.addToolBar("Extraction")
        self.toolBar.addAction(extractAction)

        fontChoice = QtWidgets.QAction(
            'Font', self)
        fontChoice.triggered.connect(self.font_choice)

        # self.toolBar = self.addToolBar("Font")
        self.toolBar.addAction(fontChoice)

        checkBox = QtWidgets.QCheckBox('Enlarge Window', self)
        checkBox.move(100, 15)
        checkBox.stateChanged.connect(self.enlarge_window)

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)

        self.btn = QtWidgets.QPushButton('Download', self)
        self.btn.move(200, 120)
        self.btn.clicked.connect(self.download)

        self.styleChoice = QtWidgets.QLabel("Macintosh", self)

        comboBox = QtWidgets.QComboBox(self)
        comboBox.addItem("motif")
        comboBox.addItem("Windows")
        comboBox.addItem("cde")
        comboBox.addItem("Plastique")
        comboBox.addItem("Cleanlooks")
        comboBox.addItem('Macintosh')
        comboBox.move(50, 250)

        self.styleChoice.move(50, 150)
        comboBox.activated[str].connect(self.style_choice)

        cal = QtWidgets.QCalendarWidget(self)
        cal.move(500, 200)
        cal.resize(200, 200)

        openEditor = QtWidgets.QAction(' &Editor', self)
        openEditor.setShortcut('Ctrl+E')
        openEditor.setStatusTip('Open Editor')
        openEditor.triggered.connect(self.editor)

        openFile = QtWidgets.QAction(" &Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open File')
        openFile.triggered.connect(self.file_open)

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(extractAction)
        fileMenu.addAction(openFile)

        editorMenu = mainMenu.addMenu(" &Editor")
        editorMenu.addAction(openEditor)

        self.show()

    def editor(self):
        self.textEdit = QtWidgets.QTextEdit()
        self.setCentralWidget(self.textEdit)

    def style_choice(self, text):
        self.styleChoice.setText(text)
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create(text))

    def download(self):

        self.completed = 0

        while self.completed < 100:
            self.completed += 0.0001
            self.progress.setValue(self.completed)

    def close_app(self):
        choice = QtWidgets.QMessageBox.question(
            self, 'Quit?', "Do you want to terminate the process?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if QtWidgets.QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def enlarge_window(self, state):
        if state == QtCore.Qt.Checked:
            self.setGeometry(50, 50, 1000, 600)
        else:
            self.setGeometry(50, 50, 500, 300)

    def font_choice(self):
        font, valid = QtWidgets.QFontDialog.getFont()
        if valid:
            self.styleChoice.setFont(font)

    def file_open(self):
        name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        file = open(name, 'r')

        self.editor()

        with file:
            text = file.read()
            self.textEdit.setText(text)


def main():
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("markt.png")))
    GUI = Window()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

print(QtWidgets.QStyleFactory.keys())
