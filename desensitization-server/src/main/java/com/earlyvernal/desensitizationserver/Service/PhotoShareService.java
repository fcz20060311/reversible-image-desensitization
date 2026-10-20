package com.earlyvernal.desensitizationserver.Service;

import com.earlyvernal.desensitizationserver.Entity.PhotoShare;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface PhotoShareService {



    /** 分享照片：加密 → 存磁盘 → 入库，返回密钥 */
    String share(Long senderId, Long receiverId, MultipartFile file);

    /** 收件箱 */
    List<PhotoShare> inbox(Long receiverId);

    /** 解密：返回原图字节 */
    byte[] decrypt(Long userId, Long shareId, String key);
}
