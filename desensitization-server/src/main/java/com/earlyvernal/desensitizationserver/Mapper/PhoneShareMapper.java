package com.earlyvernal.desensitizationserver.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.earlyvernal.desensitizationserver.Entity.PhotoShare;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface PhotoShareMapper extends BaseMapper<PhotoShare> {

    /**
     * 查某人的收件箱（带发送者昵称）
     * SQL 写在 PhotoShareMapper.xml 里
     */
    List<PhotoShare> selectInbox(@Param("receiverId") Long receiverId);
}