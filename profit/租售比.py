principal = 1  # 初始本金
rent_sale_ratio = 0.04  # 租售比
rent_growth_rate = 0.1  # 租金增利率

time = 0  # 初始时间
rent_income = 0  # 初始租金收益

while rent_income < principal:
    time += 1
    rent_income = principal * (1 + rent_growth_rate) ** time * rent_sale_ratio

print(f"需要{time}年才能实现租金收益大于等于本金")


cost = 1  # 成本
rent_sale_ratio = 0.01  # 租售比

time = 0  # 初始时间
rent_income = 0  # 初始租金收益

while rent_income <= cost:
    time += 1
    rent_income = cost * rent_sale_ratio

print(f"需要{time}年才能收回成本")
