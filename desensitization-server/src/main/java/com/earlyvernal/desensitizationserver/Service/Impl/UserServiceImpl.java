package com.earlyvernal.desensitizationserver.Service.Impl;

import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import com.earlyvernal.desensitizationserver.DTO.LoginDTO;
import com.earlyvernal.desensitizationserver.DTO.RegisterDTO;
import com.earlyvernal.desensitizationserver.Entity.User;
import com.earlyvernal.desensitizationserver.Mapper.UserMapper;
import com.earlyvernal.desensitizationserver.Service.UserService;
import com.earlyvernal.desensitizationserver.Util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.DigestUtils;
import java.nio.charset.StandardCharsets;

@Service
@Slf4j
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {


    private final UserMapper userMapper;

    @Override
    public void register(RegisterDTO dto){

        //检查用户是否已存在

        User exist=userMapper.selectByUsername(dto.getUsername());
        if(exist!=null){
            throw new RuntimeException(MessageConstant.USERNAME_EXISTS);
        }

        //保存用户
        User user =new User();
        user.setUsername(dto.getUsername());
        user.setPassword(md5(dto.getPassword()));
        user.setNickname(dto.getNickname()==null?dto.getUsername():dto.getNickname());
        userMapper.insert(user);

        log.info("用户注册成功:{}",user.getUsername());
    }

    @Override
    public String login(LoginDTO dto){
        User user=userMapper.selectByUsername(dto.getUsername());
        if(user==null||!user.getPassword().equals(md5(dto.getPassword()))){
            throw new RuntimeException(MessageConstant.LOGIN_FAILED);
        }
        log.info("用户登录成功:{}",user.getUsername());
        return JwtUtil.createToken(user.getId(),user.getUsername());
    }

    @Override
    public User getById(Long id){
        return userMapper.selectById(id);
    }

    //密码摘要
    private String md5(String raw){
        return DigestUtils.md5DigestAsHex(raw.getBytes(StandardCharsets.UTF_8));
    }


}
