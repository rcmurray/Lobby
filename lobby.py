import time
from enum import Enum
from operator import attrgetter
from operator import itemgetter

targetUsersPerRoom = 4
minUsersPerRoom = 2
maxUsersPerRoom = 6
maxWaitTimeForSubOptimalAssignment = 10          # seconds
maxWaitTimeUntilGiveUp = 60                    # seconds
maxRoomAgeForNewUsers = 300                     # seconds
fillRoomsUnderTarget = True
# fillRoomsUnderTarget = False
# overFillRooms = True
overFillRooms = False
urlPrefix = "http://bazaar.lti.cs.cmu.edu/room"
nextRoomNum = 0

# class RoomAssignmentPriority(Enum):
#     leastUsers_MaxAge = 1
#     leastUsers_MinAge = 2

roomPriority = RoomAssignmentPriority.leastUsers_MaxAge


rooms = []
availableRooms = []
roomsUnderTarget = []
users = []
unassignedUsers = []

def new_users(num_users):
    next_user_id = 0
    while next_user_id < num_users:
        next_user_id += 1
        new_user(next_user_id)
        # time.sleep(1)

def new_user(user_id):
    global users, unassignedUsers
    # If user has previously logged in
    if user_id in users:
        user = users[user_id]
        room = user['room']

        # If user already assigned to a room, reassign
        if room is not None:
            reassign_room[user,room]

        # else previously logged-in user must already be in the unassignedUsers list
        #      -- but double-checking as a failsafe
        elif user not in unassignedUsers:
            unassignedUsers.append(user)

    # This is a new user
    else:
        user = {'user_id': user_id, 'start_time': time.time(), 'room': None}
        users.append(user)
        unassignedUsers.append(user)


def reassign_room(user,room):
    print("user_id " + user['user_id'] + ": RETURN to URL " + room['url'])

def print_uus():
    print(unassignedUsers)


def assign_rooms():
    global unassignedUsers
    i = 0
    while True:
        i += 1
        if len(unassignedUsers) > 0:
            if fillRoomsUnderTarget:
                fill_rooms_under_target()
            if len(unassignedUsers) >= targetUsersPerRoom:
                assign_new_rooms(targetUsersPerRoom)
            if (len(unassignedUsers) > 0) and overFillRooms:
                overfill_rooms()
            if len(unassignedUsers) > 0:
                users_due_for_suboptimal = get_users_due_for_suboptimal()
                if len(users_due_for_suboptimal) > 0:
                    assign_new_room(len(users_due_for_suboptimal))
        unassignedUsers = prune_users()       # tell users who have been waiting too long to come back later
        time.sleep(1)


# If filling rooms that are under target before adding new rooms
def fill_rooms_under_target():
    # Assuming
    #   -- fill rooms that are most-under-target first
    #   -- fill one under-target room to target level before filling next under-target room
    global availableRooms, unassignedUsers
    availableRooms = prune_rooms(availableRooms)
    rooms_under_target = get_rooms_under_target()
    i = 0
    while (i < len(rooms_under_target)) and (len(unassignedUsers) > 0):
        assign_up_to_target(rooms_under_target[i])
        i += 1

def get_rooms_under_target():
    global availableRooms
    if len(availableRooms) == 0:
        return availableRooms
    availableRooms = prune_and_sort_rooms(availableRooms)
    rooms_under_target = []
    i = 0
    while i < len(availableRooms):
        if availableRooms[i]['num_users'] < targetUsersPerRoom:
            rooms_under_target.append(availableRooms[i])
        i += 1
    if len(rooms_under_target) > 0:
        return sort_rooms(rooms_under_target)
    else:
        return rooms_under_target

def get_users_due_for_suboptimal():
    global unassignedUsers
    users_due_for_suboptimal = []
    i = 0
    if len(unassignedUsers) > targetUsersPerRoom:   # Don't assign suboptimally if there are now target num of users
        return users_due_for_suboptimal
    while i < len(unassignedUsers):
        print("Time diff for unassignedUser(" + str(unassignedUsers[i]['user_id']) + ")" + str(time.time() - unassignedUsers[i]['start_time']))
        if (time.time() - unassignedUsers[i]['start_time']) > maxWaitTimeForSubOptimalAssignment:
            users_due_for_suboptimal.append(unassignedUsers[i])
        i += 1
    return users_due_for_suboptimal

def assign_up_to_target(room):
    global unassignedUsers
    while (room['num_users'] < targetUsersPerRoom) and (len(unassignedUsers) > 0):
        assign_room(unassignedUsers[0],room)

def add_to_room_under_target (room):
    global unassignedUsers
    room_users = room['users']
    num_under_target = targetUsersPerRoom - len(users)
    while (len(unassignedUsers) > 0) and (num_under_target > 0):
        user = unassignedUsers[0]
        assign_room(user,room)
        print("user_id " + user['user_id'] + ": assigned to room_under_target " + room['url'])
        num_under_target -= 1

def assign_new_rooms(num_users_per_room):
    global unassignedUsers
    while (len(unassignedUsers) > num_users_per_room):
        assign_new_room(num_users_per_room)

def assign_new_room(num_users):
    # url = ...        # CREATE SCHEME FOR ASSIGNING ROOM URLs
    global unassignedUsers, rooms, availableRooms, nextRoomNum
    nextRoomNum += 1
    url = urlPrefix + str(nextRoomNum)
    room = {'url': url, 'start_time': time.time(), 'users': [], 'num_users': 0}
    num_users_remaining = num_users
    while (num_users_remaining > 0) and (len(unassignedUsers) > 0):
        next_user = unassignedUsers[0]
        assign_room(next_user,room)
        num_users_remaining -= 1
    rooms.append(room)
    availableRooms.append(room)  # if no overfilling, room will soon be pruned from availableRooms

def overfill_rooms():
    global availableRooms, unassignedUsers
    availableRooms = prune_and_sort_rooms(availableRooms)
    if len(availableRooms) == 0:
        return
    next_user = unassignedUsers[0]  # users are listed in increasing start_time order
    longest_user_wait = time.time() - next_user['start_time']
    while (longest_user_wait > maxWaitTimeForSubOptimalAssignment) and (len(availableRooms) > 0):
        next_room = availableRooms[0]
        assign_room(next_user,next_room)
        availableRooms = prune_and_sort_rooms(availableRooms)
        if len(unassignedUsers) > 0:
            next_user = unassignedUsers[0]
            longest_user_wait = time.time() - next_user['start_time']
        else:
            longest_user_wait = 0   # No more users waiting

def assign_room(user,room):
    # Send user link to user_room
    global unassignedUsers
    user['room'] = room
    room['users'].append(user)
    room['num_users'] = len(room['users'])
    unassignedUsers.remove(user)
    print("user_id " + str(user['user_id']) + ": Go to URL " + room['url'])


def prune_and_sort_rooms(room_list):
    pruned_rooms = prune_rooms(room_list)
    if len(pruned_rooms) != 0:
        return sort_rooms(pruned_rooms)

def prune_rooms(room_list):
    num_rooms = len(room_list)
    i = 0
    while i < num_rooms:
        room = room_list[i]
        room_age = time.time() - room['start_time']
        room_users = room['users']
        room_slots_available = maxUsersPerRoom - len(room_users)
        # Prune rooms that are too old for new users or that are filled to max
        if (room_age >= maxRoomAgeForNewUsers) or (room_slots_available <= 0):
            del room_list[i]
            num_rooms = len(room_list)
        else:           # increment room counter 'i' only if current room was not deleted
            i += 1
    return room_list

# Sort primarily number of users (ascending), then secondarily by start_time (ascending)
#   to prioritize rooms with the least users, and secondarily with oldest start times
def sort_rooms(room_list):
    s = sorted(room_list, key=itemgetter('start_time'))
    return sorted(s,key=itemgetter('num_users'))

def prune_users():
    global unassignedUsers
    for user in unassignedUsers:
        if (time.time() - user['start_time']) >= maxWaitTimeUntilGiveUp:
            print("user_id " + str(user['user_id']) + ": I'm sorry. There are not enough other users logged in right now to start a session. Please try again later.")
            unassignedUsers.remove(user)
    return unassignedUsers


















