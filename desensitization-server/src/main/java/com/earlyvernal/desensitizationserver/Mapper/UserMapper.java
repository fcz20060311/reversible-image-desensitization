package com.earlyvernal.desensitizationserver.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.earlyvernal.desensitizationserver.Entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {

}
