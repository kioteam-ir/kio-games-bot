from orm import UserStats

_= UserStats.get_or_create(33244421)

print(_)