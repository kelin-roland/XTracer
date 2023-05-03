import csv
import json
import os


class Log:
    def __init__(self):
        self.api_header = []
        self.intent_header = []
        self.permission_header = []
        self.per_int_path = r'E:\研究生\实验\logicRegression/tmp/permission_intent_header.csv'
        self.get_header()

    def save_header(self):
        with open(self.per_int_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.intent_header)
            writer.writerow(self.permission_header)

    def get_header(self):
        if not os.path.exists(self.per_int_path):
            with open(self.per_int_path, 'w'):
                print('create pei_int_header.csv')
        else:
            with open(self.per_int_path, encoding="utf-8") as f:
                reader = csv.reader(f)
                tmp = [row for row in reader]
                if tmp:
                    self.intent_header = tmp[0]
                    self.permission_header = tmp[1]
        with open("source/hook_list_479.csv") as f:
            hookList = [row.split(',')[0] for row in f]
        del (hookList[0])
        self.api_header = hookList


def get_feature_paths(path):
    filePaths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if '.txt' in file:
                filePath = path + '\\' + file
                filePaths.append(filePath)
    return filePaths


def split_permission(arg):
    per_list = []
    if 'permission.' in arg:
        tmp_list = arg.split('permission.')
        for i in tmp_list:
            permission = i.split(',')[0]
            permission = permission.replace(']', '').replace('"', '')
            if permission.isupper():
                per_list.append(permission)
    return per_list


def split_intent(arg):
    int_list = []
    if 'action.' in arg:
        tmp_list = arg.split('action.')
        for i in tmp_list:
            intent = i.split(',')[0]
            intent = intent.replace(']', '').replace('"', '')
            if intent.isupper():
                int_list.append(intent)
    return int_list


per_int_list = [
    'android.content.Intent/$init',
    'android.content.Intent/putExtra',
    'android.content.Intent/setAction',
    'android.support.v4.app.ActivityCompat/requestPermissions',
    'androidx.core.app.ActivityCompat/requestPermissions'
]

#######以下三个函数为频率特征###########
def readJson_frequency(path):
    print(path)
    log = Log()
    with open(path, 'r') as lf:
        loadJson = json.load(lf)
        frequency_data = dict()
        for thread in loadJson:
            thread_data = loadJson[thread]
            for item in thread_data:
                api_class = item[0]
                api_method = item[1].split('(')[0]
                api_arg = item[2]
                api_full_name = api_class + "/" + api_method
                # 读取api
                if api_full_name not in per_int_list:
                    try:
                        tmp=log.api_header.index(api_full_name)
                    except:
                        print(api_full_name)
                        return None
                    if api_full_name in frequency_data:
                        frequency_data[api_full_name] += 1
                    else:
                        frequency_data[api_full_name] = 1
                # 读取permission\intent
                # else:
                #     for arg in api_arg:
                #         per_list = split_permission(arg)
                #         int_list = split_intent(arg)
                #         # print(per_list, int_list)
                #         for permission in per_list:
                #             if permission not in log.permission_header:
                #                 log.permission_header.append(permission)
                #             if permission in frequency_data:
                #                 frequency_data[permission] += 1
                #             else:
                #                 frequency_data[permission] = 1
                #         for intent in int_list:
                #             if intent not in log.intent_header:
                #                 log.intent_header.append(intent)
                #             if intent in frequency_data:
                #                 frequency_data[intent] += 1
                #             else:
                #                 frequency_data[intent] = 1
    # log.save_header()
    return frequency_data


def get_dataset_frequency(datapath):
    data_list = []
    if target_path[0]:
        for path in target_path[0]:
            for item in get_feature_paths(path):
                item_data = readJson_frequency(item)
                if item_data:
                    item_data['lx'] = 1
                    data_list.append(item_data)
    if target_path[1]:
        for path in target_path[1]:
            for item in get_feature_paths(path):
                item_data = readJson_frequency(item)
                if item_data:
                    item_data['ey'] = 1
                    data_list.append(item_data)
    log = Log()
    # field_name = log.api_header + log.permission_header + log.intent_header
    field_name = log.api_header
    field_name.insert(0, 'ey')
    field_name.insert(1, 'lx')
    fill_dict(data_list, field_name)
    with open(datapath, 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, lineterminator='\n', fieldnames=field_name)
        writer.writeheader()
        writer.writerows(data_list)


def fill_dict(data_lists, fieldname):
    new_data_list = []
    for data in data_lists:
        for item in fieldname:
            if item not in data:
                data[item] = 0
        new_data_list.append(data)
    return new_data_list

#######以下两个个函数为序列特征###########
def readJson_sequence(path, length):
    print(path)
    log = Log()
    sequence_data = []
    with open(path, 'r') as lf:
        loadJson = json.load(lf)
        for thread in loadJson:
            thread_data = loadJson[thread]
            n=len(thread_data)
            mid=n//2
            left=mid
            right=mid+1
            while left>=0 or right<n:
                if left>=0:
                    item = thread_data[left]
                    sequence_data=insert_sequence(log,item,sequence_data, length,'left')
                    if sequence_data==None:
                        return []
                    left-=1
                if right<n:
                    item = thread_data[right]
                    sequence_data=insert_sequence(log,item,sequence_data, length,'right')
                    if sequence_data==None:
                        return []
                    right+=1
    log.save_header()
    return sequence_data


def insert_sequence(log,item,sequence_data, length,direction):
    api_class = item[0]
    api_method = item[1].split('(')[0]
    api_arg = item[2]
    api_full_name = api_class + "/" + api_method
    target_list = log.api_header + log.permission_header
    if api_full_name in per_int_list:
        for arg in api_arg:
            per_list = split_permission(arg)
            for permission in per_list:
                if permission not in log.permission_header:
                    log.permission_header.append(permission)
                    target_list.append(permission)
                target = target_list.index(permission)
                if sequence_data.count(target) < length:
                    if direction=='left':
                        if target not in sequence_data[:1]:
                            sequence_data.insert(0, target)
                    elif direction=='right':
                        if target not in sequence_data[-1:]:
                            sequence_data.append(target)
    else:
        try:
            target = target_list.index(api_full_name)
            if sequence_data.count(target) < length:
                if direction=='left':
                    if target not in sequence_data[:1]:
                        sequence_data.insert(0, target)
                elif direction=='right':
                    if target not in sequence_data[-1:]:
                        sequence_data.append(target)
        except:
            return None
    return sequence_data

def get_dataset_sequence(dataset_path,length):
    data_list = []
    if target_path[0]:
        for path in target_path[0]:
            fail_count=0
            for item in get_feature_paths(path):
                item_data = readJson_sequence(item, length)
                if item_data==[]:
                    fail_count+=1
                else:
                    md5=item.split('\\')[-1].split('.txt')[0]
                    item_data.insert(0, 0)
                    item_data.insert(1, 1)
                    item_data.insert(2, md5)
                    data_list.append(item_data)
            print('========',path,':',fail_count)
    if target_path[1]:
        for path in target_path[1]:
            fail_count=0
            for item in get_feature_paths(path):
                item_data = readJson_sequence(item, length)
                if item_data==[]:
                    fail_count+=1
                else:
                    md5=item.split('\\')[-1].split('.txt')[0]
                    item_data.insert(0, 1)
                    item_data.insert(1, 0)
                    item_data.insert(2, md5)
                    data_list.append(item_data)
            print('========',path,':',fail_count)
    with open(dataset_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data_list)


if __name__ == '__main__':
    feature_path_lx = r'H:\samples\dataset_x\benign\feature'
    feature_path_ey = r'H:\samples\dataset_x\malice\feature'
    feature_path_2022_lx = r'H:\样本_年份\良性样本\2022\检测为良性_success\feature'
    feature_path_2022_ey = r'H:\样本_年份\恶意样本\2022_malware_500_new\feature'
    feature_path_2021_ey = r'H:\样本_年份\恶意样本\2021_malware_new_1510\feature'
    dataset_sequence_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_5.csv'
    dataset_sequence_mal_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_mal_5.csv'
    dataset_sequence_ben_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_ben_5.csv'
    dataset_sequence_2022_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_2022_5.csv'
    dataset_sequence_2022_benign_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_2022_benign_5.csv'
    dataset_sequence_2022_malice_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_2022_malice_5.csv'
    dataset_sequence_2021_malice_5_path = r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_2021_malice_5.csv'
    # get_dataset_frequency(dataset_frequency_path)
    # target_path = [feature_path_2022_lx, None]
    # target_path = [None,feature_path_2021_ey]
    # target_path = [feature_path_lx,feature_path_ey]
    # target_path = [None, feature_path_ey]
    # get_dataset_sequence(dataset_sequence_5_path, 5)
    # target_path = [feature_path_2022_lx, feature_path_2022_ey]
    # get_dataset_sequence(dataset_sequence_2021_malice_5_path, 5)
    ey_path=r'H:\cxl_dataset\479_api_per_intent_序列\恶意'
    ey_no_year_path=ey_path+r'\无年份'
    ey_2022_androzoo_500_3_path=ey_path+r'\2022_androzoo_500_3'
    ey_2021_androzoo_1510_path=ey_path+r'\2021_androzoo_1510'
    ey_2022_androzoo_986_6_path=ey_path+r'\2022_androzoo_986_6'
    ey_2020=ey_path+r'\2020'
    ey_paths=[ey_no_year_path,ey_2022_androzoo_500_3_path,ey_2021_androzoo_1510_path,ey_2022_androzoo_986_6_path,ey_2020]
    # ey_paths=[ey_no_year_path]

    lx_path=r'H:\cxl_dataset\479_api_per_intent_序列\良性'
    lx_no_year_path=lx_path+r'\无年份'
    lx_2021_androzoo_path=lx_path+r'\2021_androzoo'
    lx_2022_androzoo_616_path=lx_path+r'\2022_androzoo_616'
    lx_2022_androzoo_1500_path=lx_path+r'\2022_androzoo_1500'
    lx_2021=lx_path+r'\2021'
    lx_2022=lx_path+r'\2022'
    lx_paths=[lx_no_year_path,lx_2021_androzoo_path,lx_2022_androzoo_616_path,lx_2022_androzoo_1500_path,lx_2021,lx_2022]
    # lx_paths=[lx_no_year_path]

    target_path = [lx_paths,ey_paths]
    dataset_sequence_5_path_479=r'E:\研究生\实验\logicRegression\dataset\dataset_sequence_5_479.csv'
    dataset_frequency_path=r'E:\研究生\实验\特征\dataset_frequency_479_1.csv'
    get_dataset_sequence(dataset_sequence_5_path_479, 5)
    # get_dataset_frequency(dataset_frequency_path)