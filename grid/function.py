'''
入参有3个
max，min，还有一个list
找出 在max和min之间的list值
'''

def find_values_between(min_value, max_value, lst):
    result = [x for x in lst if min_value <= x <= max_value]
    return result

def downcast(amount, lot):
    return abs(amount // lot * lot)


def sortOrderByPrice(lst) :
    return sorted(lst, key=lambda order: order.price)