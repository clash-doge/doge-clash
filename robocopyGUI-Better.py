import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
                             QFileDialog, QCheckBox, QSpinBox, QFormLayout, QGroupBox, QTabWidget)
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
        self.setGeometry(100, 100, 600, 600)

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

        # 创建常用参数区域
        self.create_common_options(layout)

        # 创建高级参数区域
        self.create_advanced_options(layout)

        # 执行命令按钮和显示结果
        self.run_button = QPushButton('执行 Robocopy', self)
        self.run_button.clicked.connect(self.run_robocopy)
        layout.addWidget(self.run_button)

        # 日志选择
        self.log_label = QLabel('日志文件:')
        self.log_input = QLineEdit(self)
        self.log_btn = QPushButton('选择日志文件', self)
        self.log_btn.clicked.connect(self.browse_log)

        log_layout = QHBoxLayout()
        log_layout.addWidget(self.log_input)
        log_layout.addWidget(self.log_btn)
        layout.addWidget(self.log_label)
        layout.addLayout(log_layout)

        # 命令预览
        self.command_preview = QTextEdit(self)
        self.command_preview.setReadOnly(True)
        layout.addWidget(QLabel('命令预览:'))
        layout.addWidget(self.command_preview)

        # 输出结果
        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(QLabel('执行结果:'))
        layout.addWidget(self.result_display)

        # 设置布局
        self.setLayout(layout)

    def create_common_options(self, layout):
        common_group = QGroupBox("常用参数")
        common_layout = QVBoxLayout()

        # 常用选项：/S /E /Z /MIR
        self.s_check = QCheckBox('/S (复制子目录，不复制空子目录)', self)
        self.e_check = QCheckBox('/E (复制子目录，包括空子目录)', self)
        self.z_check = QCheckBox('/Z (可重新启动模式)', self)
        self.mir_check = QCheckBox('/MIR (镜像模式)', self)

        common_layout.addWidget(self.s_check)
        common_layout.addWidget(self.e_check)
        common_layout.addWidget(self.z_check)
        common_layout.addWidget(self.mir_check)

        common_group.setLayout(common_layout)
        layout.addWidget(common_group)

    def create_advanced_options(self, layout):
        advanced_group = QGroupBox("高级设置")
        tab_widget = QTabWidget()

        # 高级选项页1：COPY 和安全选项
        copy_tab = QWidget()
        copy_layout = QFormLayout()
        self.copy_input = QLineEdit(self)
        self.copy_input.setPlaceholderText('输入 COPY 标记（如 DAT 或 DATSOU）')
        copy_layout.addRow("COPY 参数:", self.copy_input)
        copy_tab.setLayout(copy_layout)

        # 高级选项页2：重试次数和等待时间
        retry_tab = QWidget()
        retry_layout = QFormLayout()
        self.retry_spin = QSpinBox(self)
        self.retry_spin.setValue(5)
        self.wait_spin = QSpinBox(self)
        self.wait_spin.setValue(30)
        retry_layout.addRow("重试次数:", self.retry_spin)
        retry_layout.addRow("等待时间(秒):", self.wait_spin)
        retry_tab.setLayout(retry_layout)

        tab_widget.addTab(copy_tab, "COPY 设置")
        tab_widget.addTab(retry_tab, "重试设置")

        advanced_group.setLayout(QVBoxLayout())
        advanced_group.layout().addWidget(tab_widget)
        layout.addWidget(advanced_group)

    def browse_src(self):
        src_dir = QFileDialog.getExistingDirectory(self, '选择源文件夹')
        if src_dir:
            self.src_input.setText(src_dir)

    def browse_dest(self):
        dest_dir = QFileDialog.getExistingDirectory(self, '选择目标文件夹')
        if dest_dir:
            self.dest_input.setText(dest_dir)

    def browse_log(self):
        log_file, _ = QFileDialog.getSaveFileName(self, '选择日志文件', '', '日志文件 (*.txt)')
        if log_file:
            self.log_input.setText(log_file)

    def run_robocopy(self):
        src = self.src_input.text()
        dest = self.dest_input.text()
        log_file = self.log_input.text()

        if not src or not dest:
            self.result_display.setText("请指定源和目标文件夹。")
            return

        # 构建 robocopy 命令
        command = f'robocopy "{src}" "{dest}"'

        # 添加常用选项
        if self.s_check.isChecked():
            command += ' /S'
        if self.e_check.isChecked():
            command += ' /E'
        if self.z_check.isChecked():
            command += ' /Z'
        if self.mir_check.isChecked():
            command += ' /MIR'

        # 添加高级选项
        if self.copy_input.text():
            command += f' /COPY:{self.copy_input.text()}'
        command += f' /R:{self.retry_spin.value()} /W:{self.wait_spin.value()}'

        # 添加日志文件
        if log_file:
            command += f' /LOG:"{log_file}"'

        # 在预览框中显示命令
        self.command_preview.setText(command)

        # 禁用按钮防止重复执行
        self.run_button.setEnabled(False)
        self.result_display.setText("正在执行命令，请稍候...\n")

        # 启动后台线程执行命令
        self.thread = RobocopyThread(command)
        self.thread.output_signal.connect(self.display_output)
        self.thread.start()

    def display_output(self, output):
        # 执行完成后显示结果，重新启用按钮
        self.result_display.setText(output)
        self.run_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RobocopyApp()
    ex.show()
    sys.exit(app.exec_())
