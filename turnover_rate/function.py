# def find_position(numbers, target):
#     sorted_numbers = sorted(numbers, reverse=False)  # 将数字列表按照降序排序
#     print(f"sorted:{sorted_numbers}")
#     if target in sorted_numbers:
#         position = sorted_numbers.index(target)
#         return position
#     else:
#         for i in range(len(sorted_numbers)):
#             if sorted_numbers[i] > target:
#                 return i - 1
#         return len(sorted_numbers) - 1
'''
有一个list，长度为n
对前n-1个元素排序，
如果第n个元素在新list中，返回在新list的位置
如果第n个元素不在新list中，返回第一个比这个数字大的位置-1
'''
def find_position(lst):
    lst= list(lst)
    sorted_lst = sorted(lst[:-1])
    target = lst[-1]
    # print(f"sorted:{sorted_lst}，target:{target}")
    if target in sorted_lst:
        return sorted_lst.index(target)
    else:
        for i in range(len(sorted_lst)):
            if sorted_lst[i] > target:
                return i - 1
        return len(sorted_lst) - 1

# 示例使用
# nums = [5, 3, 9, 2, 7]
# target_num = int(input("请输入一个数字: "))
# result = find_position(nums, target_num)
# print(f"数字 {target_num} 在列表中的位置值为: {result}")