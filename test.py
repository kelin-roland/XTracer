
# import XT_config
# chooseApkPath = r'H:\样本\dataset_x\benign'
# storage_path = chooseApkPath + '/0000_storage.yml'
# storage = XT_config.config(storage_path)
# if storage.data is None:
#     storage.data={}
# storage.data['123']=1
# print(storage.data)
# storage.saveData()
# print(storage.data)
# if '1' in storage.data:
#     print(1)

# import os
# def getApkPath(path):
#     apkPaths = []
#     for root, dirs, files in os.walk(path):
#         for file in files:
#             if '.apk' in file:
#                 apkPath = path + '\\' + file
#                 apkPaths.append(apkPath)
#     return apkPaths
# path=r'H:\样本\dataset_x\benign'
# apkPaths = getApkPath(path)
# for i in apkPaths:
#     fpath, fname = os.path.split(i)
#     print(fpath, fname)
# import csv
# def hook_list():
#     extend_list = [
#         'android.content.Intent/$init',
#         'android.content.Intent/putExtra',
#         'android.content.Intent/setAction',
#         'android.support.v4.app.ActivityCompat/requestPermissions',
#         'androidx.core.app.ActivityCompat/requestPermissions'
#     ]
#     with open("source/hook_list.csv") as f:
#         hookList = [row.split(',')[0] for row in f]
#     for item in extend_list:
#         hookList.append(item)
#     del(hookList[0])
#     return hookList
# a=hook_list()
# print(a)

# import sys
# sys.setrecursionlimit(5000)
# def sum(n):
#     if n > 0:
#         return 1+sum(n-1)
#     else:
#         return 0
# new_sum = sum(4900)
# print(new_sum)

# import csv
# permission_list=[1,2]
# intent_list=[3,4]
# with open('tmp/permission_intent.csv', 'w', encoding='UTF8', newline='') as f:
#     writer = csv.writer(f)
#     writer.writerow(permission_list)
#     writer.writerow(intent_list)
#
# with open('tmp/permission_intent.csv',encoding="utf-8") as f:
#     reader = csv.reader(f)
#     tmp = [row for row in reader]
#     data = []
#     for row in reader:
#         data.append(row)
#     print(tmp)
# arg="ACCESS_FINE_LOCATION""]"
# a=arg.split('android.permission.')
# list=[]
# print(a)
# for i in a:
#     per=i.split(',')[0]
#     per=per.replace(']','')
#     print(per,per.isupper())
#     list.append(per)
# print(list)
#
import hashlib

import XT_config,os
# chooseApkPath = r'H:\样本_年份\良性样本\2022\检测为良性_success'
# storage_path = chooseApkPath + '/0000_storage.yml'
# storage = XT_config.config(storage_path)
# if storage.data is None:
#     storage.data = {'0000_success_num': 0,
#                     '0000_fail_num': 0}
# for root, dirs, files in os.walk(chooseApkPath+r'\feature'):
#     for file in files:
#         if '.txt' in file:
#             storage.data['0000_success_num'] += 1
#             storage.data[file.split('.txt')[0]] = 'success'
# storage.saveData()

# with open("source/hook_list - 副本.csv") as f:
#     hookList = [row.split(',')[0] for row in f]
# print(hookList)
# del (hookList[0])

path_1=r'H:\cxl_dataset\479_api_per_intent_序列\良性\2022_androzoo_1500'
path_2=r'H:\样本_年份\良性样本\2022_androzoo_1500'
def getMD5(path):
    md = hashlib.md5()
    with open(file=path, mode='rb') as csna:
        md.update(csna.read())
    return md.hexdigest()

folder1 = path_2
md5_dict = {}
for filename in os.listdir(folder1):
    print(filename)
    if '.apk' in filename:
        file_path = os.path.join(folder1, filename)
        if os.path.isfile(file_path):
            md5 = getMD5(file_path)
            filename=filename.split('.')[0]
            md5_dict[filename] = md5

folder2 = path_1
for filename in os.listdir(folder2):
    if '.txt' in filename:
        print(filename)
        file_path = os.path.join(folder2, filename)
        fil_tmp = filename.split('.')[0]
        if os.path.isfile(file_path) and fil_tmp in md5_dict:
            md5 = md5_dict[fil_tmp]+'.txt'
            new_file_path = os.path.join(folder2, md5)
            os.rename(file_path, new_file_path)
# for filename in os.listdir(folder2):
#     if '.txt' not in filename:
#         print(filename)
#         file_path = os.path.join(folder2, filename)
#         fil_tmp = file_path+'.txt'
#         os.rename(file_path, fil_tmp)
