package com.earlyvernal.desensitizationserver.Service;

import com.earlyvernal.desensitizationserver.DTO.DesensitizeResult;

public interface PythonService {

    DesensitizeResult desensitize(byte[] imageBytes, String filename);

    byte[] restore(byte[] cipherBytes ,String key);

}
