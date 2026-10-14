package com.earlyvernal.desensitizationserver.DTO;


import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterDTO {

    @NotBlank(message= MessageConstant.USERNAME_NOT_BLANK)
    @Size(min=3,max=20,message=MessageConstant.USERNAME_SIZE)
    private String username;

    @NotBlank(message=MessageConstant.PASSWORD_NOT_BLANK)
    @Size(min=6,max=20,message=MessageConstant.PASSWORD_SIZE)
    private String password;
    private String nickname;
}
