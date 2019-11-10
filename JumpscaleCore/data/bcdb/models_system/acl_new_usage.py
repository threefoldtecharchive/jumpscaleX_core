# This file should be moved to bcdb tests directory
j.clients.ipmi.get().save()

bcdb = j.data.bcdb.system
models = list(j.data.bcdb.system.models)
user_ids = []


for i in range(10):
    u = bcdb.user.new()
    u.name = "hamada_%s" % i
    u.email = "user%s@me.com" % i
    u.dm_id = "user%s.ibiza" % i
    u.save()
    user_ids.append(u.id)

circle_admins = bcdb.circle.new()
circle_admins.name = "admina"
circle_admins.email = "admina@me.com"
circle_admins.dm_id = "admins.ibiza"
circle_admins.user_members = user_ids[4]
circle_admins.save()

circle_publishers = bcdb.circle.new()
circle_publishers.name = "publishers"
circle_publishers.email = "publishers@me.com"
circle_publishers.dm_id = "publishers.ibiza"
circle_publishers.user_members = user_ids[2:4]
circle_publishers.circle_members = [circle_admins.id]
circle_publishers.save()

circle_guests = bcdb.circle.new()
circle_guests.name = "guests"
circle_guests.email = "guests@me.com"
circle_guests.dm_id = "guests.ibiza"
circle_guests.user_members = user_ids[0:2]
circle_guests.circle_members = [circle_publishers.id]
circle_guests.save()


obj = models[-1]  # client
aa = obj.find()[0]
if not aa.acl_id:
    acl_obj = aa.acl.new()
else:
    acl_obj = aa.acl.get(aa.acl_id)

aa.acl.rights_set(acl_obj, userids=user_ids[5:7], circleids=[circle_guests.id], rights=["r"])
aa.acl.rights_set(acl_obj, userids=user_ids[7:9], circleids=[circle_publishers.id], rights=["w"])
aa.acl.rights_set(acl_obj, userids=[user_ids[9]], circleids=[circle_admins.id], rights=["d"])

assert aa.acl.rights_check(acl_obj, user_ids[4], ["r"])
assert aa.acl.rights_check(acl_obj, user_ids[4], ["d"])
assert not aa.acl.rights_check(acl_obj, user_ids[2], ["d"])

assert aa.acl.rights_check(acl_obj, circle_admins.id, ["r"])
