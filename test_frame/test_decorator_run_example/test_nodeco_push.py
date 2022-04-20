from funboost import boost
from test_no_decorator2_consume import add



add_boost_101 = boost('192_168_1_101__add_queue')(add)
add_boost_102 = boost('192_168_1_102__add_queue')(add)

add_boost_101.push(5,6)
add_boost_102.push(7,8)

