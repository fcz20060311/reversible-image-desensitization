package com.earlyvernal.desensitizationserver.Service;

import com.earlyvernal.desensitizationserver.DTO.LoginDTO;
import com.earlyvernal.desensitizationserver.DTO.RegisterDTO;
import com.earlyvernal.desensitizationserver.Entity.User;

public interface UserService {

    void register(RegisterDTO dto);

    String login(LoginDTO dto);

    User getById(Long id);
}
