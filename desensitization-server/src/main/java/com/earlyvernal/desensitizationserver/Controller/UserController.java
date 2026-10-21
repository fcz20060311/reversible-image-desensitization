package com.earlyvernal.desensitizationserver.Controller;


import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import com.earlyvernal.desensitizationserver.Common.Result;
import com.earlyvernal.desensitizationserver.DTO.LoginDTO;
import com.earlyvernal.desensitizationserver.DTO.RegisterDTO;
import com.earlyvernal.desensitizationserver.Entity.User;
import com.earlyvernal.desensitizationserver.Service.UserService;
import com.earlyvernal.desensitizationserver.Util.JwtUtil;
import com.earlyvernal.desensitizationserver.VO.UserVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    //注册
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO dto){
         userService.register(dto);
         return Result.success();
    }


    //登录
    @PostMapping("/login")
    public Result<String> login(@Valid @RequestBody LoginDTO dto){
        return Result.success(userService.login(dto));
    }

    //当前用户:从请求头获取token,解析出userId
    @GetMapping("/me")
    public Result<UserVO> me(@RequestHeader("Authorization") String token){
        Long userId= JwtUtil.getUserId(token);
        User user=userService.getById(userId);

        if(user==null){
            return Result.error(MessageConstant.USERNAME_NOT_EXISTS);
        }

        UserVO userVO=new UserVO();

        userVO.setId(user.getId());
        userVO.setUsername(user.getUsername());
        userVO.setNickname(user.getNickname());

        return Result.success(userVO);
    }

}
