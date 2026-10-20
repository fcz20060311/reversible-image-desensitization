package com.earlyvernal.desensitizationserver.Mapper;


import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.earlyvernal.desensitizationserver.Entity.PhotoShare;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface PhotoShareMapper extends BaseMapper<PhotoShare>{

    List<PhotoShare> selectInbox(@Param("receiverId")Long receiverId);
}
