import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QCheckBox, QSpinBox, QFormLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# 创建一个QThread子类来执行robocopy命令
class RobocopyThread(QThread):
    # 定义信号，用于向主线程发送命令输出
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            # 执行robocopy命令
            result = subprocess.run(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout if result.stdout else result.stderr
        except Exception as e:
            output = str(e)

        # 将结果发送到主线程
        self.output_signal.emit(output)

class RobocopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('Robocopy 命令生成器')
        self.setGeometry(100, 100, 600, 500)

        # 布局
        layout = QVBoxLayout()

        # 源文件夹选择
        self.src_label = QLabel('源文件夹:', self)
        self.src_input = QLineEdit(self)
        self.src_btn = QPushButton('浏览', self)
        self.src_btn.clicked.connect(self.browse_src)

        src_layout = QHBoxLayout()
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(self.src_btn)

        layout.addWidget(self.src_label)
        layout.addLayout(src_layout)

        # 目标文件夹选择
        self.dest_label = QLabel('目标文件夹:', self)
        self.dest_input = QLineEdit(self)
        self.dest_btn = QPushButton('浏览', self)
        self.dest_btn.clicked.connect(self.browse_dest)

        dest_layout = QHBoxLayout()
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(self.dest_btn)

        layout.addWidget(self.dest_label)
        layout.addLayout(dest_layout)

        # robocopy 参数部分
        self.mirror_check = QCheckBox('/MIR (镜像模式)', self)
        self.restartable_check = QCheckBox('/Z (断点续传)', self)
        self.verbosity_check = QCheckBox('/V (详细输出)', self)
        self.purge_check = QCheckBox('/PURGE (删除目标多余文件)', self)

        # 复制重试次数和等待时间
        retry_label = QLabel('重试次数:')
        self.retry_spin = QSpinBox(self)
        self.retry_spin.setValue(5)
        
        wait_label = QLabel('等待时间（秒）:')
        self.wait_spin = QSpinBox(self)
        self.wait_spin.setValue(30)

        form_layout = QFormLayout()
        form_layout.addRow(retry_label, self.retry_spin)
        form_layout.addRow(wait_label, self.wait_spin)

        layout.addWidget(self.mirror_check)
        layout.addWidget(self.restartable_check)
        layout.addWidget(self.verbosity_check)
        layout.addWidget(self.purge_check)
        layout.addLayout(form_layout)

        # 执行命令按钮和显示结果
        self.run_button = QPushButton('执行 Robocopy', self)
        self.run_button.clicked.connect(self.run_robocopy)
        layout.addWidget(self.run_button)

        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        # 设置布局
        self.setLayout(layout)

    def browse_src(self):
        # 打开文件夹选择对话框
        src_dir = QFileDialog.getExistingDirectory(self, '选择源文件夹')
        if src_dir:
            self.src_input.setText(src_dir)

    def browse_dest(self):
        # 打开文件夹选择对话框
        dest_dir = QFileDialog.getExistingDirectory(self, '选择目标文件夹')
        if dest_dir:
            self.dest_input.setText(dest_dir)

    def run_robocopy(self):
        # 获取源和目标路径
        src = self.src_input.text()
        dest = self.dest_input.text()

        if not src or not dest:
            self.result_display.setText("请指定源和目标文件夹。")
            return

        # 构建 robocopy 命令
        command = f'robocopy "{src}" "{dest}"'

        # 添加选中的参数
        if self.mirror_check.isChecked():
            command += ' /MIR'
        if self.restartable_check.isChecked():
            command += ' /Z'
        if self.verbosity_check.isChecked():
            command += ' /V'
        if self.purge_check.isChecked():
            command += ' /PURGE'

        # 重试和等待时间
        retries = self.retry_spin.value()
        wait_time = self.wait_spin.value()
        command += f' /R:{retries} /W:{wait_time}'

        # 禁用按钮防止重复执行
        self.run_button.setEnabled(False)
        self.result_display.setText("正在执行命令，请稍候...\n")

        # 启动一个后台线程来执行命令
        self.thread = RobocopyThread(command)
        self.thread.output_signal.connect(self.display_output)
        self.thread.start()

    def display_output(self, output):
        # 当后台线程完成命令执行时，显示结果并重新启用按钮
        self.result_display.setText(output)
        self.run_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RobocopyApp()
    ex.show()
    sys.exit(app.exec_())
