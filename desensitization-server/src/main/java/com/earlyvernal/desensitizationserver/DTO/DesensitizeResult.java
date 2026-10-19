package com.earlyvernal.desensitizationserver.DTO;

import lombok.Data;

@Data
public class DesensitizeResult {

    private String key;

    private byte[] cipherBytes;

    private Integer regionCount;
}
