package com.earlyvernal.desensitizationserver.DTO;


import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterDTO {

    @NotBlank(message="用户不能为空")
    @Size(min=3,max=20,message="密码长度需3~20位")
    private String username;

    @NotBlank(message="密码不能为空")
    @Size(min=6,max=20,message="密码长度需6~20位")
    private String password;
    private String nickname;
}
