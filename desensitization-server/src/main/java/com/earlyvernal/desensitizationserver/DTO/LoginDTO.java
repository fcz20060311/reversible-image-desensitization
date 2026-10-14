package com.earlyvernal.desensitizationserver.DTO;


import com.earlyvernal.desensitizationserver.Common.MessageConstant;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LoginDTO {

    @NotBlank(message= MessageConstant.USERNAME_NOT_BLANK)
    private String username;

    @NotBlank(message=MessageConstant.PASSWORD_NOT_BLANK)
    private String password;

}
