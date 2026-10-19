package com.earlyvernal.desensitizationserver.Service.Impl;

import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import com.earlyvernal.desensitizationserver.DTO.DesensitizeResult;
import com.earlyvernal.desensitizationserver.DTO.PythonDesensitizeResp;
import com.earlyvernal.desensitizationserver.DTO.PythonRestoreResp;
import com.earlyvernal.desensitizationserver.Service.PythonService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Base64;

@Service
@RequiredArgsConstructor
public class PythonServiceImpl implements PythonService {

    private final RestTemplate restTemplate;

    @Value("${python.base-url}")
    private String baseUrl;

    @Override
    public DesensitizeResult desensitize(byte[] imageBytes, String filename) {

        //组装 multipart 请求体
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("files", new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() {
                return filename;
            }
        });
        body.add("mode", "region");

        //请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        //发送请求
        PythonDesensitizeResp resp = restTemplate.postForObject(
                baseUrl + "/batch_desensitize", request, PythonDesensitizeResp.class);

        //校验 + 提取
        if (resp == null || resp.getImages() == null || resp.getImages().isEmpty()) {
            throw new RuntimeException(MessageConstant.PYTHON_SERVICE_ERROR);
        }
        PythonDesensitizeResp.Img img = resp.getImages().get(0);
        DesensitizeResult result = new DesensitizeResult();
        result.setKey(resp.getKey());
        result.setCipherBytes(Base64.getDecoder().decode(img.getImageBase64()));
        result.setRegionCount(img.getRegionCount());
        return result;
    }

    @Override
    public byte[] restore(byte[] cipherBytes, String key) {

        //组装请求体
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("key", key);
        body.add("files", new ByteArrayResource(cipherBytes) {
            @Override
            public String getFilename() {
                return "cipher.png";
            }
        });

        //请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        //发请求
        PythonRestoreResp resp = restTemplate.postForObject(
                baseUrl + "/batch_restore", request, PythonRestoreResp.class);

        //校验
        if (resp == null || resp.getResults() == null || resp.getResults().isEmpty()) {
            throw new RuntimeException(MessageConstant.PYTHON_SERVICE_ERROR);
        }
        PythonRestoreResp.Item item = resp.getResults().get(0);
        if (!Boolean.TRUE.equals(item.getOk())) {
            throw new RuntimeException(
                    item.getError() == null ? MessageConstant.DECRYPT_FAILED : item.getError());
        }

        return Base64.getDecoder().decode(item.getImageBase64());
    }
}
