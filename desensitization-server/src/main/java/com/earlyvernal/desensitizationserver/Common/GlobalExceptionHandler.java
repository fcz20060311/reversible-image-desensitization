package com.earlyvernal.desensitizationserver.Common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;


@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {


    //业务异常
    @ExceptionHandler(RuntimeException.class)
    public Result<Void> handleRuntimeException(RuntimeException e){
        log.warn("业务异常:{}",e.getMessage());
        return Result.error(e.getMessage());
    }

    //参数校验异常
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValidationException(MethodArgumentNotValidException e){
        String msg="参数校验失败";
        if(e.getBindingResult().getFieldError()!=null){
            msg=e.getBindingResult().getFieldError().getDefaultMessage();
        }
        log.warn("参数校验失败:{}",msg);
        return Result.error(msg);
    }

    //其他没预料的异常
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e){
        log.error("系统异常",e);
        return Result.error("系统繁忙，请稍后重试");
    }
}
