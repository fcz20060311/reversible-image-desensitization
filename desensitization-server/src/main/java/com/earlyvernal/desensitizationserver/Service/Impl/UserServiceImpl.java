package com.earlyvernal.desensitizationserver.Service.Impl;

import com.earlyvernal.desensitizationserver.DTO.RegisterDTO;
import com.earlyvernal.desensitizationserver.Mapper.UserMapper;
import com.earlyvernal.desensitizationserver.Service.UserService;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RestController;

@Service
@RestController
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    @Override
    public void register(RegisterDTO dto){

        User
    }

}
