package com.earlyvernal.desensitizationserver.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.earlyvernal.desensitizationserver.Entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    //按用户名查用户
    User selectByUsername(@Param("username") String username);
}
