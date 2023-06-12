




dict1 = {-1:1,3:1,2:1,4:0,5:1}


def get_max_offset_1():
    sorted_keys = sorted(dict1.keys())
    dict_new = {key: dict1[key] for key in sorted_keys}

    max_offset_1 = None
    last_v = None
    for_times = 0
    for k,v in dict_new.items():
        print(k,v)
        for_times+=1
        if for_times == 1:
            if v == 1:
                max_offset_1 = k
            else:
                break
        else:
            if v ==1 and last_v ==1:
                max_offset_1 = k
            else:
                break
        last_v = v
    return max_offset_1

if __name__ == '__main__':
    print(get_max_offset_1())

