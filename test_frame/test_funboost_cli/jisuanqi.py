

import fire
import re

class Calculator:
    def __init__(self):
        self.value = 0

    def evaluate(self, expression):
        expression = expression.replace(' ', '')  # 去除空格
        expression = re.sub(r'(\d+)', r'self.add(\1)', expression)  # 将数字替换为self.add(num)
        expression = expression.replace('+', '.add')  # 将+替换为.add
        expression = expression.replace('-', '.subtract')  # 将-替换为.subtract
        expression = expression.replace('*', '.multiply')  # 将*替换为.multiply
        expression = expression.replace('/', '.divide')  # 将/替换为.divide
        eval(expression)  # 执行表达式

    def add(self, num):
        self.value += num

    def subtract(self, num):
        self.value -= num

    def multiply(self, num):
        self.value *= num

    def divide(self, num):
        self.value /= num

    def __str__(self):
        return str(self.value)

def main():
    fire.Fire(Calculator)

if __name__ == "__main__":
    main()