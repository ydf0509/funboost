
import fire

class Calculator:

  def __init__(self):
    self.result = 0
    self.express = '0'

  def __str__(self):
    print('完成')
    # return f'{self.express} = {self.result}'
    return ''

  def add(self, x):
    self.result += x
    self.express = f'{self.express}+{x}'
    return self

  def sub(self, x):
    self.result -= x
    self.express = f'{self.express}-{x}'
    return self

  def mul(self, x):
    self.result *= x
    self.express = f'({self.express})*{x}'
    return self

  def div(self, x):
    self.result /= x
    self.express = f'({self.express})/{x}'
    return self

if __name__ == '__main__':
  fire.Fire(Calculator)