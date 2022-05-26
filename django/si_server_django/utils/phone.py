from phone import Phone

def getPhoneInfo(phoneNum):
    info = Phone().find(phoneNum)
    return info
# try:
#     phone = info['phone']
#     province = info['province']
#     city = info['city']
#     zip_code = info['zip_code']
#     area_code = info['area_code']
#     phone_type = info['phone_type']
# except:
#     print('none')