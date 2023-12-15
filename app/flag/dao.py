from typing import List, Optional, Tuple
from app.flag.typedef import Flag, GetFlagBy, GetFlagByWithType
from util.database import Dao


class FlagDao(Dao):
    fields = 'id, user_id, location_x, location_y, content, type, create_time, pictures, is_open'

    def add(self, flag: Flag) -> int:
        sql = ('insert into flag '
               '(user_id, location_x, location_y, content, type, is_open, create_time, update_time, pictures) '
               'values(:user_id, :location_x, :location_y, :content, :type, :is_open, '
               'current_timestamp, current_timestamp, array[]::text[]) returning id')
        return self.execute(sql, user_id=flag.user_id, content=flag.content, is_open=flag.is_open,
                            location_x=flag.location[0], location_y=flag.location[1], type=flag.type)

    def update(self, flag: Flag) -> Optional[int]:
        sql = 'update flag set pictures=:pictures where id=:id returning id'
        return self.execute(sql, id=flag.id, pictures=flag.pictures)

    def get_flag_by_flag(self, flag_id: int, user_id: int) -> Optional[Flag]:
        sql = f'select {self.fields} from flag where id=:flag_id and (is_open=1 or user_id=:user_id)'
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: int, private_id: int, get: GetFlagBy) -> List[Flag]:
        sql = (f'select {self.fields} from flag where '
               'user_id=:private_id or (is_open=1 and user_id=:user_id) '
               f'order by {get.order} {get.asc}')
        return self.execute(sql, user_id=user_id, private_id=private_id)

    def get_flag_by_location(self, user_id: int, get: GetFlagByWithType) -> List[Flag]:
        sql = (f'select {self.fields} from flag where '
               '(user_id=:user_id or is_open=1) and type=:type and '
               'location_x<:location_x_add and location_x>:location_x_sub and '
               'location_y<:location_y_add and location_y>:location_y_sub '
               f'order by {get.order} {get.asc}')
        return self.execute(sql, user_id=user_id, type=get.type,
                            location_x_add=get.key[0] + get.distance[0],
                            location_x_sub=get.key[0] - get.distance[0],
                            location_y_add=get.key[1] + get.distance[1],
                            location_y_sub=get.key[1] - get.distance[1],
                            )

    def get_flag_by_location_count(self, user_id: int, get: GetFlagByWithType) -> int:
        sql = (f'select count(1) from flag where '
               '(user_id=:user_id or is_open=1) and type=:type and '
               'location_x<:location_x_add and location_x>:location_x_sub and '
               'location_y<:location_y_add and location_y>:location_y_sub ')
        return self.execute(sql, user_id=user_id, type=get.type,
                            location_x_add=get.key[0] + get.distance[0],
                            location_x_sub=get.key[0] - get.distance[0],
                            location_y_add=get.key[1] + get.distance[1],
                            location_y_sub=get.key[1] - get.distance[1],
                            )

    def set_flag_type(self, user_id: int, flag_id: int, flag_type: int):
        sql = 'update flag set type=:flag_type where id=:flag_id and user_id=:user_id'
        self.execute(sql, user_id=user_id, flag_id=flag_id, flag_type=flag_type)


dao = FlagDao()
