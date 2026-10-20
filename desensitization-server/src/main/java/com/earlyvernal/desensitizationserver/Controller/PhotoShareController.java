package com.earlyvernal.desensitizationserver.Controller;

import com.earlyvernal.desensitizationserver.Common.Result;
import com.earlyvernal.desensitizationserver.Entity.PhotoShare;
import com.earlyvernal.desensitizationserver.Service.PhotoShareService;
import com.earlyvernal.desensitizationserver.Util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Base64;
import java.util.List;

@RestController
@RequestMapping("/api/photo")
@RequiredArgsConstructor
public class PhotoShareController {

    private final PhotoShareService photoShareService;

    /** 分享照片：上传 + 指定接收者 → 返回密钥 */
    @PostMapping("/share")
    public Result<String> share(@RequestHeader("Authorization") String token,
                                @RequestParam("receiverId") Long receiverId,
                                @RequestParam("file") MultipartFile file) {
        Long senderId = JwtUtil.getUserId(token);
        return Result.success(photoShareService.share(senderId, receiverId, file));
    }

    /** 收件箱：我收到的所有加密照片 */
    @GetMapping("/inbox")
    public Result<List<PhotoShare>> inbox(@RequestHeader("Authorization") String token) {
        Long userId = JwtUtil.getUserId(token);
        return Result.success(photoShareService.inbox(userId));
    }

    /** 解密：提供密钥 → 返回还原后的图片（base64） */
    @PostMapping("/{id}/decrypt")
    public Result<String> decrypt(@RequestHeader("Authorization") String token,
                                  @PathVariable("id") Long id,
                                  @RequestParam("key") String key) {
        Long userId = JwtUtil.getUserId(token);
        byte[] plain = photoShareService.decrypt(userId, id, key);
        return Result.success(Base64.getEncoder().encodeToString(plain));
    }
}
