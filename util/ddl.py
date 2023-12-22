d1 = '''
create table test (f1 int, f2 text, f3 int[], f4 text[], f5 json);
'''

# 用户表
d2 = '''
create table users (
id uuid primary key, 

nickname text not null,
username text not null, 
password text not null,
phone int,
is_man bool,

wechat_id text,

signature text,
profile_picture text,
background_picture text,

create_time timestamp not null,
vip_deadline timestamp,
block_deadline timestamp,
alive_deadline timestamp,
belong text,
location geometry,
extend1 text,
extend2 text,
extend3 text,
UNIQUE(username),
UNIQUE(wechat_id)
);
'''

# 关注表
d3 = '''
create table follow(
fans_id uuid not null,
star_id uuid not null,
primary key(fans_id, star_id),
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX fans_index ON follow(fans_id);
CREATE INDEX star_index ON follow(star_id);
'''

# 注销表
d4 = '''
create table sign_out_users (
user_id uuid primary key,
out_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
)
'''

# flag表
d5 = '''
create table flag (
id uuid primary key,
user_id int not null,
location geometry not null,
content text,
type int,
is_open int not null,
create_time timestamp not null,
update_time timestamp not null,
pictures text[] not null,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX type_index ON flag(type);
CREATE INDEX is_open_index ON flag(is_open);
CREATE INDEX user_id_index ON flag(user_id);
CREATE INDEX flag_location_index ON flag(location);
'''

# 评论表
d6 = '''
create table flag_comment(
id serial primary key,
flag_id uuid not null,
user_id uuid not null,
content text not null,
root_comment_id int,
distance int not null,
prefix text,
comment_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX flag_comment_index ON flag_comment(flag_id);
CREATE INDEX root_comment_index ON flag_comment(root_comment_id);
'''

# 黑名单
d7 = '''
create table black_list(
user_id uuid not null,
black_id uuid not null,
update_time timestamp,
primary key(user_id, black_id),
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX user_black_index ON black_list(user_id);
'''

# 消息
d8 = '''
create table message(
id serial primary key,
type int not null,
send_id int not null,
receive_id int not null,
content text not null,
create_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX receive_id_message_index ON message(receive_id);
'''

# 收藏表
d9 = '''

'''