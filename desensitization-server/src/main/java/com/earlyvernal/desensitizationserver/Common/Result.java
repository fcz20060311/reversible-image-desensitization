package com.earlyvernal.desensitizationserver.Common;


import lombok.Data;

@Data
public class Result<T>{
    private Integer code;
    private String msg;
    private T data;

    //成功(无数据)
    public static <T> Result<T> success(){
        Result<T> r = new Result<>();
        r.code=1;
        r.msg="success";
        return r;
    }

    //成功带数据
    public static <T> Result<T> success(T data){
        Result<T> r =new Result<>();
        r.code=1;
        r.msg="success";
        r.data=data;
        return r;
    }

    //失败
    public static <T> Result<T> error(String msg){
        Result<T> r=new Result<>();
        r.code=0;
        r.msg=msg;
        return r;
    }

}