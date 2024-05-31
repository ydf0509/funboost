from llist import sllist

# 创建一个空的链表
ll = sllist()

# 在链表的尾部添加节点
ll.append(1)

# 在链表的头部添加节点
ll.appendleft(2)

# 删除指定节点
ll.remove(1)

# 获取链表的长度
length = len(ll)

# 遍历链表
for node in ll:
    print(node.value)
