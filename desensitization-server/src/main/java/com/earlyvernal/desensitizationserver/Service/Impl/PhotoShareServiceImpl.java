package com.earlyvernal.desensitizationserver.Service.Impl;

import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import com.earlyvernal.desensitizationserver.DTO.DesensitizeResult;
import com.earlyvernal.desensitizationserver.Entity.PhotoShare;
import com.earlyvernal.desensitizationserver.Mapper.PhotoShareMapper;
import com.earlyvernal.desensitizationserver.Service.PhotoShareService;
import com.earlyvernal.desensitizationserver.Service.PythonService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class PhotoShareServiceImpl implements PhotoShareService {

    /** 密文存放目录 */
    private static final String UPLOAD_DIR = "uploads";

    private final PhotoShareMapper photoShareMapper;
    private final PythonService pythonService;

    @Override
    public String share(Long senderId, Long receiverId, MultipartFile file) {
        try {
            // 1. 读图片字节
            byte[] bytes = file.getBytes();

            // 2. 调 Python 加密
            DesensitizeResult enc = pythonService.desensitize(bytes, file.getOriginalFilename());

            // 3. 密文存磁盘（UUID 防重名）
            String filename = UUID.randomUUID() + ".png";
            Path path = Paths.get(UPLOAD_DIR, filename);
            Files.createDirectories(path.getParent());
            Files.write(path, enc.getCipherBytes());

            // 4. 入库
            PhotoShare ps = new PhotoShare();
            ps.setSenderId(senderId);
            ps.setReceiverId(receiverId);
            ps.setFilename(file.getOriginalFilename());
            ps.setFilePath(path.toString());
            ps.setKeySha256(sha256(enc.getKey()));
            photoShareMapper.insert(ps);

            log.info("照片分享成功: {} -> {}, 文件: {}", senderId, receiverId, filename);

            // 5. 返回密钥（服务器不存，由发送者交给接收者）
            return enc.getKey();

        } catch (IOException e) {
            log.error("文件处理失败", e);
            throw new RuntimeException(MessageConstant.FILE_PROCESS_FAILED);
        }
    }

    @Override
    public List<PhotoShare> inbox(Long receiverId) {
        return photoShareMapper.selectInbox(receiverId);
    }

    @Override
    public byte[] decrypt(Long userId, Long shareId, String key) {
        // 1. 查记录
        PhotoShare ps = photoShareMapper.selectById(shareId);
        if (ps == null) {
            throw new RuntimeException(MessageConstant.PHOTO_NOT_FOUND);
        }

        // 2. 权限校验：只有接收者能解密
        if (!ps.getReceiverId().equals(userId)) {
            throw new RuntimeException(MessageConstant.NO_PERMISSION);
        }

        // 3. 读密文 + 调 Python 解密
        try {
            byte[] cipher = Files.readAllBytes(Paths.get(ps.getFilePath()));
            return pythonService.restore(cipher, key);
        } catch (IOException e) {
            log.error("文件读取失败", e);
            throw new RuntimeException(MessageConstant.FILE_READ_FAILED);
        }
    }

    /** 计算密钥指纹（SHA-256 十六进制） */
    private String sha256(String raw) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }
}
