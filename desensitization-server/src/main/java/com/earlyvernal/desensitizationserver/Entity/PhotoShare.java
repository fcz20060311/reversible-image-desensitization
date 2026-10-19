package com.earlyvernal.desensitizationserver.Entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 加密照片分享记录，对应 photo_share 表
 */
@Data
@TableName("photo_share")
public class PhotoShare {

    /** 分享ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** 发送者用户ID */
    private Long senderId;

    /** 接收者用户ID */
    private Long receiverId;

    /** 原始文件名 */
    private String filename;

    /** 密文文件在磁盘上的路径 */
    private String filePath;

    /** 密钥指纹（不是明文密钥） */
    private String keySha256;

    /** 发送时间 */
    private LocalDateTime createTime;

    /**
     * 发送者昵称（不是数据库字段，是 JOIN 查出来的）
     * @TableField(exist = false) 告诉 MyBatis-Plus：这不是表里的列
     */
    @TableField(exist = false)
    private String senderName;
}