import pyvisa

rm = pyvisa.ResourceManager()

print("VISA backend:")
print(rm)

print("\nThiết bị tìm thấy:")
resources = rm.list_resources()

for resource in resources:
    print("  ", resource)
    