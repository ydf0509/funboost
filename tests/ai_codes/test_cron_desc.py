
from cron_descriptor import get_description, Options

opts = Options()
opts.locale_code = 'zh_CN'
opts.use_24hour_time_format = True # Try to force 24h format if available option

print(f"Testing '0 0 1 1 *' with default options:")
print(get_description("0 0 1 1 *", opts))


opts2 = Options()
opts2.locale_code = 'zh_CN'
opts2.use_24hour_time_format = False
print(f"Testing '0 0 1 1 *' with 24hour=False:")
print(get_description("0 0 1 1 *", opts2))

# Maybe it's a library issue with 0 hour translation
print(f"Testing '0 12 1 1 *':")
print(get_description("0 12 1 1 *", opts))
