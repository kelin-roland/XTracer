# -*- coding: utf-8 -*-
import json
import sys
import threading
import time
import frida
import subprocess
import os
from copy import copy
from PyQt5.QtWidgets import *
import XT_config
from multiprocessing import Process

sys.setrecursionlimit(5000)
# 选择hook方式  single/mult
hook_mode = 'single'

# 选择路径
# chooseApkPath = r'H:\samples\dataset_x\malice'
feature_path_lx = r'H:\samples\dataset_x\benign'
feature_path_2022_lx = r'H:\样本_年份\良性样本\2022\检测为良性_fail'
# feature_path_2022_ey = r'H:\样本_年份\恶意样本\2022_malware_500_new'
feature_path_2022_ey = r'H:\样本_年份\恶意样本\2021_malware_new_1510'

chooseApkPath = feature_path_2022_ey

storage_path = chooseApkPath + '/0000_storage.yml'
featurePath = chooseApkPath + r'/feature'
if not os.path.exists(featurePath):
    os.makedirs(featurePath)
# 记录检测结果
storage = XT_config.config(storage_path)
if storage.data is None:
    storage.data = {'0000_success_num': 0,
                    '0000_fail_num': 0}
XT = None
scripts = []
loadingAPK = ''
hookSuccess = False
run_state = 1


class XTracerData:
    def __init__(self, tracer=None):
        super(XTracerData, self).__init__()
        self.tracer = tracer

    def stop(self):
        global scripts
        for s in copy(scripts):
            try:
                s.unload()
            except frida.InvalidOperationError as e:
                print(e)
                scripts.remove(s)
            else:
                scripts.remove(s)
        print('[G] success unload script')

    def clean(self):
        self.tracer.thread_map = {}

    def export(self):
        global loadingAPK, hookSuccess
        fpath, fname = os.path.split(loadingAPK)
        api = fname.split('.apk')[0]
        jobfile = featurePath + '//' + api + '.txt'
        thread_map = self.tracer.thread_map.copy()
        if thread_map != {}:
            json.dump(thread_map, open(jobfile, 'w', encoding='utf-8'))
            hookSuccess = True
            print('[G] success get jsonLog')
        else:
            print('[G] jsonLog is None')


class XTracer:
    def __init__(self, ):
        global XT
        XT = self
        self.application_label = None
        self.packageName = None
        self.tracer = QApplication(sys.argv)
        self.trace_data = XTracerData(self)
        self.thread_map = {}
        self.hookComplete = 'false'
        if 'single' in hook_mode:
            self.singleTrace()
        elif 'mult' in hook_mode:
            self.multTrace()
        sys.exit()

    def method_entry(self, tid, clazz, method, args):
        data_list = []
        if tid in self.thread_map:
            data_list = self.thread_map[tid]
        data_list.append([clazz, method, args])
        self.thread_map[tid] = data_list

    def log(self, text):
        text = time.strftime('%Y-%m-%d %H:%M:%S:  [*] ', time.localtime(time.time())) + text
        print(text)

    # 批量检测
    # def multTrace(self):
    #     global loadingAPK
    #     apkPaths = getApkPath(chooseApkPath)
    #     if not apkPaths:
    #         print('当前文件夹已无apk')
    #         return
    #     count = 0
    #     for apkPath in apkPaths:
    #         loadingAPK = apkPath
    #         fpath, fname = os.path.split(loadingAPK)
    #         apk_name = fname.split('.apk')[0]
    #         # 是否检测过
    #         if apk_name in storage.data:
    #             continue
    #         if count == 0:
    #             print('[A] ------------------ start---------------------------')
    #         else:
    #             print('    ------------------ end %d' % count + ' APK ----------------------')
    #         count += 1
    #         if self.appTrace():
    #             storage.data[apk_name] = 'success'
    #             storage.data['0000_success_num'] += 1
    #             print("[J] Trace Success")
    #         else:
    #             storage.data[apk_name] = 'fail'
    #             storage.data['0000_fail_num'] += 1
    #             print("[J] Trace Fail")
    #         storage.saveData()
    #     print('    ------------------ end %d' % count + ' APK ----------------------')

    # 单独检测
    def singleTrace(self):
        global loadingAPK, run_state
        run_state = 0
        apkPaths = getApkPath(chooseApkPath)
        apk_index = 0
        while True:
            loadingAPK = apkPaths[apk_index]
            fpath, fname = os.path.split(loadingAPK)
            apk_name = fname.split('.apk')[0]
            if apk_name in storage.data:
                apk_index += 1
                if apk_index == len(apkPaths):
                    print('当前文件夹已无apk')
                    return
            else:
                break
        print('[A] ------------------ start ---------------------------')
        if self.appTrace():
            storage.data[apk_name] = 'success'
            storage.data['0000_success_num'] += 1
            print("[J] Trace Success ", loadingAPK)
        else:
            storage.data[apk_name] = 'fail'
            storage.data['0000_fail_num'] += 1
            print("[J] Trace Fail ", loadingAPK)
        storage.saveData()
        print('    ------------------ end -----------------------------')
        run_state = 1

    def appTrace(self):
        global hookSuccess
        print('[A] apk_Path:' + str(loadingAPK))
        self.application_label = getPackageLabel()
        self.packageName = getPackageName()
        packageActivity = getPackageActivity()
        # 判断文件是否存在
        if self.packageName is None or packageActivity is None:
            return False
        if apkInstall():
            # 清空上个程序运行残留
            self.trace_data.clean()
            # 运行安装apk
            if runApk(self.packageName, packageActivity):
                # 运行追踪脚本
                if self.runTrace():
                    # 运行monkey
                    runMonkey(self.packageName)
                    # 获取日志
                    self.getJsonLog()
                    # 获取日志后卸载脚本
                    self.trace_data.stop()
                # 无论运行是否成功，都结束运行
                stopApk(self.packageName)
            # 最后卸载app
            apkUninstall(self.packageName)
        if hookSuccess:
            # 初始化hookSuccess
            hookSuccess = False
            return True
        return False

    def runTrace(self):
        print('[E] ------------------ hooking ------------------------')
        threading.Thread(target=self.start_trace).start()
        while True:
            if 'true' in self.hookComplete:
                print('[E] success hook')
                # 重新初始化hookComplete
                self.hookComplete = 'false'
                return True
            if 'fail' in self.hookComplete:
                print('[E] fail hook')
                # 重新初始化hookComplete
                self.hookComplete = 'false'
                return False
            time.sleep(1)

    def start_trace(self):
        global scripts
        hook_process_num = 0
        def _attach(pid):
            failcount = 0
            try:
                session = device.attach(pid)
                session.enable_child_gating()
                source = open('XTracer.js', 'r', encoding='utf-8').read().replace('{hook_list}', str(hook_list()))
                script = session.create_script(source)
                script.on("message", self.FridaReceive)
                script.load()
                scripts.append(script)
                return True
            except frida.ProcessNotFoundError:
                print('[E] fail find process: ' + str(pid))
                return
            except frida.NotSupportedError as e:
                print('[E] NotSupportedError:' + str(e))
                return
            except frida.PermissionDeniedError as e:
                print('[E] PermissionDeniedError:' + str(e))
                return
            except frida.ProtocolError as e:
                print('[E] ProtocolError:' + str(e))
                return
            except frida.TransportError as e:
                print('[E] TransportError:' + str(e))
                if 'timeout was reached' in str(e):
                    return
                failcount += 1
                if failcount > 4:
                    printRed('[E] fail connect')
                    return
                # _attach(pid, failcount)

        def _on_child_added(child):
            print('[E] hook child_process:', child)
            _attach(child.pid)

        device = frida.get_usb_device()
        device.on("child-added", _on_child_added)
        for process in device.enumerate_processes():
            if self.packageName:
                if self.packageName in process.name:
                    print('[E] hook process:', process)
                    if _attach(process.pid):
                        hook_process_num += 1
            elif self.application_label:
                if self.application_label in process.name:
                    print('[E] hook process:', process)
                    if _attach(process.pid):
                        hook_process_num += 1
            # if self.packageName in process.name or self.application_label in process.name:
            #     print('[E] hook process:', process)
            #     if _attach(process.pid):
            #         hook_process_num += 1
        # 若无attach成功则判断hook失败
        time.sleep(5)
        if hook_process_num == 0:
            print('[E] hook process failed')
            self.hookComplete = 'fail'
            return

    def FridaReceive(self, message, data):
        if message['type'] == 'send':
            if message['payload'][:10] == 'XTracer:::':
                packet = json.loads(message['payload'][10:])
                cmd = packet['cmd']
                data = packet['data']
                if cmd == 'log':
                    # 接收hook完成日志
                    if 'Hook Complete' in data:
                        self.hookComplete = 'true'
                elif cmd == 'enter':
                    tid, cls, method, args = data
                    XT.method_entry(tid, cls, method, args)
                # elif cmd == 'exit':
                #     tid, retval = data
                #     XT.method_exit(tid, retval)
        else:
            print(message['stack'])

    def getJsonLog(self):
        print('[G] ------------------ get jsonLog --------------------')
        self.trace_data.export()


def hook_list():
    extend_list = [
        'android.content.Intent/$init',
        'android.content.Intent/putExtra',
        'android.content.Intent/setAction',
        'android.support.v4.app.ActivityCompat/requestPermissions',
        'androidx.core.app.ActivityCompat/requestPermissions'
    ]
    with open("source/hook_list.csv") as f:
        hookList = [row.split(',')[0] for row in f]
    for item in extend_list:
        hookList.append(item)
    del (hookList[0])
    return hookList


def getApkPath(path):
    apkPaths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if '.apk' in file:
                apkPath = path + '\\' + file
                apkPaths.append(apkPath)
    return apkPaths


def runCMD(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
    return result


def getPackageLabel():
    adbReturn = runCMD('aapt dump badging ' + loadingAPK + '| findstr application-label:')
    if 'application-label' in adbReturn:
        labelName = adbReturn.split("application-label:'")[1].split("'")[0]
        print('[B] labelName: ' + labelName)
        return labelName
    else:
        return None


def getPackageName():
    adbReturn = runCMD('aapt dump badging ' + loadingAPK + '| findstr package')
    if 'package: name' in adbReturn:
        package_name = adbReturn.split("package: name='")[1].split("' versionCode")[0]
        print('[B] package_name: ' + package_name)
        return package_name
    else:
        # print('[B] fail get package_name--adbReturn:', adbReturn)
        printRed('[B] fail get package_name--apkPath:' + loadingAPK)
        return None


def getPackageActivity():
    adbReturn = runCMD('aapt dump badging ' + loadingAPK + '| findstr activity')
    if 'activity: name' in adbReturn:
        activityName = adbReturn.split("activity: name='")[1].split("'  label")[0]
        print('[B] mainActivityName: ' + activityName)
        return activityName
    else:
        printRed('[B] fail get activityName--apkPath:' + loadingAPK)
        return None


def apkInstall():
    print('[C] ------------------ APK installing -----------------')
    command = 'adb install -r ' + loadingAPK
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(180)
        for readLine in adbReturn:
            if 'Success' in str(readLine):
                print('[C] APK install success')
                return True
        return False
    except subprocess.TimeoutExpired:
        printRed('[C] APK install fail--apkPath:' + loadingAPK)
        return False


def runApk(package, packageActivity):
    print('[D] ------------------ APK running --------------------')
    command = 'adb shell am start -W -n ' + package + '/' + packageActivity
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=60)
        if 'Complete' in str(adbReturn):
            print('[D] start running')
            # 关闭线程
            proc.kill()
            time.sleep(1)
            return True
    except subprocess.TimeoutExpired:
        proc.kill()
        printRed('[D] fail run--TimeoutExpired')
        return False


def runMonkey(package):
    print('[F] ------------------ monkey running -----------------')
    command = 'adb shell CLASSPATH=/sdcard/monkey.jar:/sdcard/framework.jar exec app_process /system/bin tv.panda.test.monkey.Monkey -p ' + package + ' --uiautomatormix --pct-reset 0 --pct-rotation 0 --running-minutes 2 -v'
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=300)
        for readline in adbReturn:
            if ' Monkey finished' in str(readline):
                print('[F] success monkey')
                return
    except subprocess.TimeoutExpired:
        printRed('[F] fail run monkey')


def stopApk(package):
    print('[H] ------------------ app stopping -------------------')
    command = 'adb shell pm clear ' + package
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=120)
        if 'Success' in str(adbReturn):
            print('[H] success stopping')
            return
    except subprocess.TimeoutExpired:
        printRed('[H] fail stop')


def apkUninstall(package):
    print('[I] ------------------ uninstalling -------------------')
    command = 'adb uninstall ' + package
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=120)
        for readLine in adbReturn:
            if 'Success' in str(readLine):
                print('[I] uninstalled')
                return
    except subprocess.TimeoutExpired:
        printRed('[I] fail uninstall')


def printRed(message):
    print("\033[1;31;48m" + message + "\033[0m")


if __name__ == '__main__':
    while True:
        if run_state:
            adbReturn = subprocess.run('frida-ps -U', shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
            if "Failed" in adbReturn:
                print('Frida Disconnect, Waiting Frida')
            if "PID" in adbReturn:
                hookThread = Process(target=XTracer)
                hookThread.start()
                hookThread.join()
        else:
            print(run_state)
        time.sleep(10)
