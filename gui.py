#! ./.venv/Scripts/python.exe
# coding:utf-8


import sys
import io
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QTextEdit, QFileDialog, QSpinBox
from PyQt5.QtGui import QIcon,QTextCursor
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from seq_video import Seq_conv
import resources
# pyrcc5 resources.qrc -o resources.py
# pyinstaller --onefile --windowed --icon=./GUI/weedy.ico gui.py

class Path:
    # 样本文件路径
    # model 路径
    model_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku/hachiroku_0.model"

    # visual 路径
    visual_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku/hachiroku_0.visual"

    # mfm 路径
    mfm_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku/hachiroku_0.mfm"

    # geo 路径
    geo_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku/hachiroku_0.geometry"

    # 视频文件路径
    video_path = "Video/output_86anim.mp4"

    # 统一名称(生成的文件的名称将为 name+_编号)
    name = "hachiroku"

    # 帧间隔(每 frame_inter 帧抽一帧)(作为参考,1秒12帧左右能最低限度地保证观感上的流畅,过高的帧数会导致模型数的增加,游戏引擎可能会无法承受)
    frame_inter = 3

    # 存储路径
    # seq 存储路径
    seq_save_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/ssm_seq"
    # model,visual,mfm,dds与geo 存储路径
    model_save_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku"
    # model,visual,mfm 中对应的地址(精确到文件夹,文件名由脚本补全)
    model_content_path = "PnFMods/8620_Hayate/JSD510_Hayate/ship/model/hachiroku"

# 自定义流类，用于重定向标准输出
class EmittingStream(QObject):
    textWritten = pyqtSignal(str)  # 定义一个信号，当有文本写入时发射
    
    def write(self, text):
        self.textWritten.emit(str(text))
    
    def flush(self):
        pass

# 工作线程类，用于在后台执行模块
class ModuleWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, module_function, *args, **kwargs):
        super().__init__()
        self.module_function = module_function
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            # 检查 module_function 是否可调用
            if not callable(self.module_function):
                self.error.emit(f"错误: {self.module_function} 不是可调用对象")
                return
                
            # 执行模块函数
            result = self.module_function(*self.args, **self.kwargs)
            self.finished.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.old_stdout = None  # 保存原来的标准输出
        self.emitting_stream = None  # 自定义输出流
        self.worker = None  # 工作线程
       
        # 设置窗口标题和大小
        self.setWindowTitle("seq转换器")
        self.setGeometry(100, 100, 1200, 570)  # x, y, width, height
        # 锁定窗口大小
        self.setFixedSize(1200,570)
        # 设置窗口图标和背景
        self.setWindowIcon(QIcon(":/GUI/weedy.ico"))
        self.setStyleSheet("""
            QMainWindow {
                background-image: url(:/GUI/background.png);
                background-repeat: no-repeat;
                background-position: center;
            }
        """)
       
        
        #输入部分 0
        self.label = QLabel("输入设置:", self)
        self.label.move(10, 0)

        # model_path 30
        self.modelpath_label = QLabel("model 路径:", self)
        self.modelpath_label.move(10, 30)

        self.modelpath_textbox = QTextEdit(Path.model_path, self)
        self.modelpath_textbox.setGeometry(80, 30,1000,30)

        self.modelpath_button = QPushButton("...", self)
        self.modelpath_button.setGeometry(1090, 30,30,30)
        self.modelpath_button.clicked.connect(self.modelpath_button_clicked)

        # visual_path  70
        self.visualpath_label = QLabel("visual路径:", self)
        self.visualpath_label.move(10, 70)

        self.visualpath_textbox = QTextEdit(Path.visual_path, self)
        self.visualpath_textbox.setGeometry(80, 70,1000,30)

        self.visualpath_button = QPushButton("...", self)
        self.visualpath_button.setGeometry(1090, 70,30,30)
        self.visualpath_button.clicked.connect(self.visualpath_button_clicked)

        # mfm_path  110
        self.mfmpath_label = QLabel("  mfm 路径:", self)
        self.mfmpath_label.move(10, 110)

        self.mfmpath_textbox = QTextEdit(Path.mfm_path, self)
        self.mfmpath_textbox.setGeometry(80, 110,1000,30)

        self.mfmpath_button = QPushButton("...", self)
        self.mfmpath_button.setGeometry(1090, 110,30,30)
        self.mfmpath_button.clicked.connect(self.mfmpath_button_clicked)

        # geo_path 150
        self.geopath_label = QLabel("  geo 路径:", self)
        self.geopath_label.move(10, 150)

        self.geopath_textbox = QTextEdit(Path.geo_path, self)
        self.geopath_textbox.setGeometry(80, 150,1000,30)

        self.geopath_button = QPushButton("...", self)
        self.geopath_button.setGeometry(1090, 150,30,30)
        self.geopath_button.clicked.connect(self.geopath_button_clicked)

        # video_path 190
        self.videopath_label = QLabel("  动画路径:", self)
        self.videopath_label.setToolTip('使用gif和apng两种支持透明通道的动画文件时会将dds保存为DXT5(支持透明)格式\n其余为DXT1格式')
        self.videopath_label.move(10, 190)

        self.videopath_textbox = QTextEdit(Path.video_path, self)
        self.videopath_textbox.setGeometry(80, 190,1000,30)

        self.videopath_button = QPushButton("...", self)
        self.videopath_button.setGeometry(1090, 190,30,30)
        self.videopath_button.clicked.connect(self.videopath_button_clicked)

        # 输出参数 240
        self.output_label = QLabel("输出参数:", self)
        self.output_label.move(10, 240)

        # name  270
        self.name_label = QLabel("  工程名称:", self)
        self.name_label.setToolTip('生成的文件的名称将为 工程名称+_编号')
        self.name_label.move(10, 270)

        self.name_textbox = QTextEdit(Path.name, self)
        self.name_textbox.setGeometry(80, 270,400,30)

        # frame_inter 310
        self.frameinter_label = QLabel("    帧间隔:", self)
        self.frameinter_label.move(10, 310)

        self.frameinter_box = QSpinBox(self)
        self.frameinter_box.setValue(Path.frame_inter)
        self.frameinter_label.setToolTip('每 [填入的数字] 帧抽一帧\n作为参考,1秒12帧左右能最低限度地保证观感上的流畅\n过高的帧数会导致模型数的增加,游戏引擎可能会无法承受')
        self.frameinter_box.setGeometry(80, 310,40,30)

        # 存储路径 360
        self.savepath_label = QLabel("存储路径:", self)
        self.savepath_label.move(10,360)

        # seq 存储路径 390
        self.seqsavepath_label = QLabel(" seq 存储路径:", self)
        self.seqsavepath_label.setGeometry(10,390,170,30)

        self.seqsavepath_textbox = QTextEdit(Path.seq_save_path, self)
        self.seqsavepath_textbox.setGeometry(180, 390,900,30)

        self.seqsavepath_button = QPushButton("...", self)
        self.seqsavepath_button.setGeometry(1090, 390,30,30)
        self.seqsavepath_button.clicked.connect(self.seqsavepath_button_clicked)

        # model,visual,mfm,dds与geo 存储路径 
        self.modelsavepath_label = QLabel(" model类文件存储路径:", self)
        self.modelsavepath_label.setToolTip('model,visual,mfm,dds与geometry 文件的存储路径 ')
        self.modelsavepath_label.setGeometry(10,430,170,30)

        self.modelsavepath_textbox = QTextEdit(Path.model_save_path, self)
        self.modelsavepath_textbox.setGeometry(180, 430,900,30)

        self.modelsavepath_button = QPushButton("...", self)
        self.modelsavepath_button.setGeometry(1090, 430,30,30)
        self.modelsavepath_button.clicked.connect(self.modelsavepath_button_clicked)

        # model,visual,mfm 中对应的地址(精确到文件夹,文件名由脚本补全)
        self.modelcontentpath_label = QLabel("model,visual,mfm 中的地址:", self)
        self.modelcontentpath_label.setToolTip('参照例子填入 model,visual,mfm 中对应的下一级文件的地址\n内容参考model类文件存储路径,精确到文件夹,文件名由脚本补全\n形如:PnFMods/[Mod_Name]]/[Ship_ID]/***/***')
        self.modelcontentpath_label.setGeometry(10,470,170,30)

        self.modelcontentpath_textbox = QTextEdit(Path.model_content_path, self)
        self.modelcontentpath_textbox.setGeometry(180, 470,900,30)

        # 生成按钮
        self.generater_button = QPushButton("开始生成", self)
        self.generater_button.setGeometry(1090, 530, 100, 30)
        self.generater_button.clicked.connect(self.generater_button_clicked)

        # 输出日志
        self.log_label = QLabel(" 日志:", self)
        self.log_label.setToolTip('显示执行过程中的部分信息')
        self.log_label.setGeometry(10,500,170,30)

        self.log_textbox = QTextEdit(self)
        self.log_textbox.setGeometry(80, 505,900,60)

         # 设置输出重定向
        self.setup_output_redirection()
    
    def setup_output_redirection(self):
        """设置输出重定向"""
        # 保存原来的标准输出
        self.old_stdout = sys.stdout
        
        # 创建自定义流
        self.emitting_stream = EmittingStream()
        self.emitting_stream.textWritten.connect(self.append_output)
        
        # 重定向标准输出
        sys.stdout = self.emitting_stream
        
    def modelpath_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '打开model文件',filter= 'model文件(*.model)')
        self.modelpath_textbox.setText(filepath)

    def visualpath_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '打开visual文件',filter= 'visual文件(*.visual)')
        self.visualpath_textbox.setText(filepath)

    def mfmpath_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '打开mfm文件',filter= 'mfm文件(*.mfm)')
        self.mfmpath_textbox.setText(filepath)

    def geopath_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '打开geometry文件',filter= 'geo文件(*.geometry)')
        self.geopath_textbox.setText(filepath)

    def videopath_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '打开动画文件',filter="所有文件(*);;gif文件(*.gif);;mp4文件(*.mp4);;apng文件(*.apng)",initialFilter='gif文件(*.gif)')
        self.videopath_textbox.setText(filepath)

    def seqsavepath_button_clicked(self):
        directory = QFileDialog.getExistingDirectory(None,"选择seq保存目录","")
        self.seqsavepath_textbox.setText(directory)

    def modelsavepath_button_clicked(self):
        directory = QFileDialog.getExistingDirectory(None,"选择model类文件目录","")
        self.modelsavepath_textbox.setText(directory)

    def generater_button_clicked(self):
        # 清空输出
        self.log_textbox.clear()
        # 禁用按钮，防止重复执行
        self.generater_button.setEnabled(False)
        Path.model_path = self.modelpath_textbox.toPlainText()
        Path.visual_path = self.visualpath_textbox.toPlainText()
        Path.mfm_path = self.mfmpath_textbox.toPlainText()
        Path.geo_path = self.geopath_textbox.toPlainText()
        Path.video_path = self.videopath_textbox.toPlainText()

        Path.name = self.name_textbox.toPlainText()
        Path.frame_inter = self.frameinter_box.value()

        Path.seq_save_path = self.seqsavepath_textbox.toPlainText()
        Path.model_save_path = self.modelsavepath_textbox.toPlainText()
        Path.model_content_path = self.modelcontentpath_textbox.toPlainText()

        # 创建工作线程并执行模块
        self.worker = ModuleWorker(Seq_conv.seq_generater,Path)
        self.worker.finished.connect(self.on_module_finished)
        self.worker.error.connect(self.on_module_error)
        self.worker.start()

    @pyqtSlot(str)
    def append_output(self, text):
        """向文本编辑框添加输出"""
        cursor = self.log_textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.log_textbox.setTextCursor(cursor)
        self.log_textbox.ensureCursorVisible()
    
    def on_module_finished(self, result):
        """模块执行完成"""
        self.append_output(f"模块执行完成\n")
        self.generater_button.setEnabled(True)
    
    def on_module_error(self, error_msg):
        """模块执行出错"""
        self.append_output(f"模块执行出错: {error_msg}\n")
        self.generater_button.setEnabled(True)
    
    def closeEvent(self, event):
        """窗口关闭时恢复标准输出"""
        if self.old_stdout:
            sys.stdout = self.old_stdout
        super().closeEvent(event)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())