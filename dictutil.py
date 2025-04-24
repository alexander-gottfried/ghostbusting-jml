def dict_entry_set_add(dic, key, item):
    if key not in dic:
        dic[key] = set()
    dic[key].add(item)
