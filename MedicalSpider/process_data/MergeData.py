import os
import re
import json


def get_data_file(path='./'):
    """# match data json file names in the pattern of 'disease-xxx-xxx.json'"""
    pattern = re.compile(r'disease-\d+-.*')
    p = re.compile(r'\d+')
    filenames = os.listdir(path)
    datafiles = []
    for name in filenames:
        if re.search(pattern, name):
            datafiles.append(path + name)
    return sorted(datafiles, key=lambda x: int(x[re.search(p, x).span()[0]:re.search(p, x).span()[1]]))


def process_data(paths):
    diseases = []
    for path in paths:
        disease_data = open(path, 'r', encoding='UTF-8').readlines()
        for data in disease_data:
            disease = json.loads(data)
            diseases.append(disease)
    return diseases


def merge(diseases: dict):    # 接收过来是字典
    set_dis = set()
    print('Original diseases: %d' % len(diseases))
    f = open(datadir + 'medical.json', 'a', encoding='UTF-8')
    for disease in diseases:
        disease['cure_dept'] = [dept + '科' for dept in disease['cure_dept'].split('科') if dept]
        if disease.get('treat'):
            disease['treat'] = [treat for treat in disease['treat'].split(' ') if treat]
        else:
            disease['treat'] = []
        disease = json.dumps(disease, ensure_ascii=False)
        set_dis.add(disease)
    set_dis = list(set_dis)
    sort_set_dis = sorted(set_dis, key=lambda x: int(json.loads(x)['id']))
    print('Set diseases: %d' % len(sort_set_dis))
    # print('Total words count %d' % len())
    # f.writelines(sort_set_dis)
    for disease in sort_set_dis:
        f.write(disease + '\n')
    f.close()


def check_id(diseases):
    """
    check how many replicate ids of diseases, and print the
    difference of the set of all disease['id'] and set of numbers
    """
    set_ids = set()
    dic = dict()
    with open(datadir + 'numbers.csv', 'r', encoding="UTF-8") as f:
        numbers = f.readlines()
        numbers = list(map(str.strip, numbers))
    print('Original numbers: %d' % len(numbers))
    numbers = set(numbers)
    print('Set numbers: %d' % len(numbers))
    for disease in diseases:
        tmp = dic.get(disease['id'])
        if tmp:
            dic.update({disease['id']: tmp+1})
        else:
            dic.update({disease['id']: 1})
        set_ids.add(disease['id'])
    print('Original ids: %d' % len(diseases))
    print('Set ids: %d' % len(set_ids))
    print('set_numbers - set_ids difference: %s' % (numbers - set_ids))
    # i = 0
    # for disease in diseases:
    #     tmp = dic.get(disease['id'])
    #     if tmp > 1:
    #         print('replicate id: %s: %s' % (disease['id'], tmp))
    #         i += 1
    # print('total replicate: %d' % i)


if __name__ == '__main__':
    datadir = '../data/'
    datafiles = get_data_file(datadir)
    print(datafiles)
    diseases = process_data(datafiles)
    # merge(diseases)
    check_id(diseases)
